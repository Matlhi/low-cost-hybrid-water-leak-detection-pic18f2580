/*
 * AquaDetection - Pipe Leak Detector
 * Target: PIC18F2580 @ 20 MHz
 *
 * v7.3 - DISPLAY-FIRST DESIGN
 *
 * Key behaviour change from v7.2:
 *   - Once a leak position is found, the LCD ALWAYS shows the position.
 *   - Acoustic localisation runs every cycle in the background and
 *     silently updates g_shown_pos_mm; the display refreshes only when
 *     the new result differs by more than POSITION_TOL_MM.
 *   - The LCD never reverts to "CHECKING FLOW..." or "LOCATING..." while
 *     a confirmed leak is active.
 *   - Only when 3 consecutive flow-clear readings are obtained does the
 *     display return to "NO LEAK / SYSTEM NORMAL".
 *
 * LCD state machine (simplified):
 *   FLOW       -> flow difference detected          -> LEAK_CONFIRM
 *   LEAK_CONFIRM -> 3 consecutive leak readings     -> POSITION
 *   POSITION   -> localization running in bg,        stays POSITION
 *                 display updates if pos changes
 *   POSITION   -> 3 consecutive clear flow readings -> CLEAR
 *   CLEAR      -> leak detected again               -> LEAK_CONFIRM
 */

#include <xc.h>
#include <stdint.h>

#define _XTAL_FREQ 20000000UL

#pragma config OSC = HS
#pragma config WDT = OFF
#pragma config PWRT = ON
#pragma config BOREN = BOHW
#pragma config WRT0 = OFF
#pragma config WRT1 = OFF
#pragma config WRT2 = OFF
#pragma config WRT3 = OFF
#pragma config WRTB = OFF
#pragma config WRTC = OFF
#pragma config WRTD = OFF
#pragma config CP0 = OFF
#pragma config CP1 = OFF
#pragma config CP2 = OFF
#pragma config CP3 = OFF
#pragma config CPB = OFF
#pragma config CPD = OFF
#pragma config PBADEN = OFF
#pragma config LVP = OFF
#pragma config XINST = OFF
#pragma config DEBUG = OFF

/* ------------------------------------------------------------------ */
/* Pin assignments                                                      */
/* ------------------------------------------------------------------ */
#define LCD_RS LATBbits.LATB2
#define LCD_EN LATBbits.LATB3
#define LCD_D4 LATBbits.LATB4
#define LCD_D5 LATBbits.LATB5
#define LCD_D6 LATBbits.LATB6
#define LCD_D7 LATBbits.LATB7

#define LED_RED LATCbits.LATC1
#define LED_GREEN LATCbits.LATC2

#define FLOW1_PIN PORTBbits.RB0
#define FLOW2_PIN PORTBbits.RB1

/* ------------------------------------------------------------------ */
/* Tuning constants                                                     */
/* ------------------------------------------------------------------ */
#define FLOW_WINDOW_MS 50u
#define FLOW_DIFF_THRESHOLD 2u
#define FLOW_CONFIRM_COUNT 3u
#define FLOW_DEBOUNCE_US 50u

#define SAMPLE_COUNT 32u
#define MAX_LAG 10
#define PIPE_LENGTH_MM 1000L
#define SOUND_SPEED_MPS 338L
#define INTER_SAMPLE_US 172u
#define SAMPLE_PERIOD_US     291L  /* calibrated: 2x ADC_Read + INTER_SAMPLE_US */
#define ADC_INTER_CH_BIAS_US  40L  /* AN1 sampled ~40us after AN0 in each iteration */
#define LAG_AVG_COUNT 7u
#define ENERGY_THRESHOLD 2000UL
#define POSITION_TOL_MM 15u

#define TMR1H_RELOAD 0x0B
#define TMR1L_RELOAD 0xDC

/* ------------------------------------------------------------------ */
/* State machine                                                        */
/* ------------------------------------------------------------------ */
typedef enum
{
    STATE_FLOW_CHECK = 0, /* Monitoring flow, no confirmed leak      */
    STATE_LEAK_CONFIRM,   /* Leak detected, accumulating confirmations */
    STATE_POSITION,       /* Leak confirmed - show position always   */
    STATE_CLEAR           /* Flow clear confirmed                    */
} SystemState;

/* ------------------------------------------------------------------ */
/* Types                                                                */
/* ------------------------------------------------------------------ */
typedef struct
{
    uint16_t count1;
    uint16_t count2;
    uint16_t diff;
} FlowWindowResult;

/* ------------------------------------------------------------------ */
/* Globals                                                              */
/* ------------------------------------------------------------------ */
static int16_t g_micA[SAMPLE_COUNT];
static int16_t g_micB[SAMPLE_COUNT];

static volatile uint8_t g_timer1_flag = 0;
static uint16_t g_elapsed_sec = 0;

static SystemState g_state = STATE_FLOW_CHECK;
static uint8_t g_leak_confirm = 0u;
static uint8_t g_clear_confirm = 0u;

/* Last position successfully displayed */
static uint16_t g_shown_pos_s1_mm = 0xFFFFu;

/* ------------------------------------------------------------------ */
/* Prototypes                                                           */
/* ------------------------------------------------------------------ */
static void Timer1_Init(void);
void __interrupt() isr(void);
static void UART_Init(void);
static void UART_Write(char ch);
static void UART_Print(const char *text);
static void UART_PrintUInt2(uint16_t value);
static void UART_PrintUInt(uint16_t value);
static void UART_PrintTimestamp(void);
static void UART_Log(const char *text);
static void LCD_WriteNibble(uint8_t nibble);
static void LCD_SendCommand(uint8_t cmd);
static void LCD_SendCommandLong(uint8_t cmd);
static void LCD_SendChar(uint8_t ch);
static void LCD_Print(const char *text);
static void LCD_SetCursor(uint8_t row, uint8_t col);
static void LCD_PrintUInt(uint16_t value, uint8_t width);
static void LCD_Init(void);
static void LCD_ShowChecking(void);
static void LCD_ShowLeakFound(void);
static void LCD_ShowPosition(uint16_t s1_mm, uint16_t s2_mm);
static void LCD_ShowNoLeak(void);
static void ADC_Init(void);
static uint16_t ADC_Read(uint8_t channel);
static void IO_Init(void);
static FlowWindowResult Flow_CountWindow(void);
static uint32_t Acoustic_MeasureEnergy(void);
static void Acoustic_CaptureSamples(void);
static int16_t Acoustic_FindBestLag(void);
static uint16_t Acoustic_PositionFromLag(int16_t lag_q4);
static uint16_t Acoustic_Locate(uint16_t previous_position_mm);
static uint16_t AbsDiffU16(uint16_t a, uint16_t b);
static void Startup(void);

/* ------------------------------------------------------------------ */
/* Timer 1 ISR - 1-second tick                                         */
/* ------------------------------------------------------------------ */
static void Timer1_Init(void)
{
    T1CON = 0x30;
    TMR1H = TMR1H_RELOAD;
    TMR1L = TMR1L_RELOAD;
    PIR1bits.TMR1IF = 0;
    PIE1bits.TMR1IE = 1;
    INTCONbits.PEIE = 1;
    INTCONbits.GIE = 1;
    T1CONbits.TMR1ON = 1;
}

void __interrupt() isr(void)
{
    if (PIR1bits.TMR1IF)
    {
        PIR1bits.TMR1IF = 0;
        TMR1H = TMR1H_RELOAD;
        TMR1L = TMR1L_RELOAD;
        g_timer1_flag = 1;
    }
}

/* ------------------------------------------------------------------ */
/* UART                                                                 */
/* ------------------------------------------------------------------ */
static void UART_Init(void)
{
    TRISCbits.TRISC6 = 0;
    TRISCbits.TRISC7 = 1;
    SPBRG = 129;
    TXSTAbits.BRGH = 1;
    TXSTAbits.SYNC = 0;
    TXSTAbits.TXEN = 1;
    RCSTAbits.SPEN = 1;
    RCSTAbits.CREN = 1;
}

static void UART_Write(char ch)
{
    while (!TXSTAbits.TRMT)
    {
        ;
    }
    TXREG = ch;
}

static void UART_Print(const char *text)
{
    while (*text != '\0')
    {
        UART_Write(*text++);
    }
}

static void UART_PrintUInt2(uint16_t value)
{
    if (value > 99u)
    {
        value = 99u;
    }
    UART_Write((char)('0' + (value / 10u)));
    UART_Write((char)('0' + (value % 10u)));
}

static void UART_PrintUInt(uint16_t value)
{
    char digits[6];
    uint8_t count = 0u;

    if (value == 0u)
    {
        UART_Write('0');
        return;
    }

    while (value > 0u)
    {
        digits[count++] = (char)('0' + (value % 10u));
        value /= 10u;
    }
    while (count > 0u)
    {
        UART_Write(digits[--count]);
    }
}

static void UART_PrintTimestamp(void)
{
    UART_Write('[');
    UART_PrintUInt2(g_elapsed_sec / 60u);
    UART_Write(':');
    UART_PrintUInt2(g_elapsed_sec % 60u);
    UART_Write(']');
    UART_Write(' ');
}

static void UART_Log(const char *text)
{
    UART_PrintTimestamp();
    UART_Print(text);
    UART_Print("\r\n");
}

/* ------------------------------------------------------------------ */
/* LCD                                                                  */
/* ------------------------------------------------------------------ */
static void LCD_WriteNibble(uint8_t nibble)
{
    LCD_D4 = (nibble >> 0) & 1u;
    LCD_D5 = (nibble >> 1) & 1u;
    LCD_D6 = (nibble >> 2) & 1u;
    LCD_D7 = (nibble >> 3) & 1u;
    LCD_EN = 1;
    __delay_us(1);
    LCD_EN = 0;
    __delay_us(50);
}

static void LCD_SendCommand(uint8_t cmd)
{
    LCD_RS = 0;
    LCD_WriteNibble((uint8_t)(cmd >> 4));
    LCD_WriteNibble((uint8_t)(cmd & 0x0Fu));
}

static void LCD_SendCommandLong(uint8_t cmd)
{
    LCD_SendCommand(cmd);
    __delay_ms(2);
}

static void LCD_SendChar(uint8_t ch)
{
    LCD_RS = 1;
    LCD_WriteNibble((uint8_t)(ch >> 4));
    LCD_WriteNibble((uint8_t)(ch & 0x0Fu));
}

static void LCD_Print(const char *text)
{
    while (*text != '\0')
    {
        LCD_SendChar((uint8_t)*text++);
    }
}

static void LCD_SetCursor(uint8_t row, uint8_t col)
{
    LCD_SendCommand((row == 0u) ? (uint8_t)(0x80u + col)
                                : (uint8_t)(0xC0u + col));
    __delay_us(50);
}

static void LCD_PrintUInt(uint16_t value, uint8_t width)
{
    char digits[6];
    uint8_t count = 0u;
    uint8_t written = 0u;

    if (value == 0u)
    {
        LCD_SendChar('0');
        written = 1u;
    }
    else
    {
        while (value > 0u)
        {
            digits[count++] = (char)('0' + (value % 10u));
            value /= 10u;
        }
        while (count > 0u)
        {
            LCD_SendChar((uint8_t)digits[--count]);
            written++;
        }
    }

    while (written < width)
    {
        LCD_SendChar(' ');
        written++;
    }
}

static void LCD_Init(void)
{
    __delay_ms(20);
    LCD_SendCommandLong(0x02);
    LCD_SendCommand(0x28);
    LCD_SendCommand(0x0C);
    LCD_SendCommand(0x06);
    LCD_SendCommandLong(0x01);
}

static void LCD_ShowChecking(void)
{
    LCD_SetCursor(0, 0);
    LCD_Print("CHECKING FLOW...");
    LCD_SetCursor(1, 0);
    LCD_Print("COUNTING...     ");
}

static void LCD_ShowLeakFound(void)
{
    LCD_SetCursor(0, 0);
    LCD_Print("!! LEAK FOUND !!");
    LCD_SetCursor(1, 0);
    LCD_Print("LOCATING...     ");
}

static void LCD_ShowPosition(uint16_t s1_mm, uint16_t s2_mm)
{
    LCD_SetCursor(0, 0);
    LCD_Print("S1:");
    LCD_PrintUInt(s1_mm, 4);
    LCD_Print("mm       ");

    LCD_SetCursor(1, 0);
    LCD_Print("S2:");
    LCD_PrintUInt(s2_mm, 4);
    LCD_Print("mm       ");
}

static void LCD_ShowNoLeak(void)
{
    LCD_SetCursor(0, 0);
    LCD_Print("   NO  LEAK     ");
    LCD_SetCursor(1, 0);
    LCD_Print(" SYSTEM NORMAL  ");
}

/* ------------------------------------------------------------------ */
/* ADC                                                                  */
/* ------------------------------------------------------------------ */
static void ADC_Init(void)
{
    ADCON0 = 0x01;
    ADCON1 = 0x0D;
    ADCON2 = 0x92;
}

static uint16_t ADC_Read(uint8_t channel)
{
    ADCON0bits.CHS = channel;
    __delay_us(25);
    ADCON0bits.GO_DONE = 1;
    while (ADCON0bits.GO_DONE)
    {
        ;
    }
    return (((uint16_t)ADRESH) << 8) | ADRESL;
}

/* ------------------------------------------------------------------ */
/* IO                                                                   */
/* ------------------------------------------------------------------ */
static void IO_Init(void)
{
    TRISA = 0xFF;

    TRISCbits.TRISC1 = 0;
    TRISCbits.TRISC2 = 0;

    TRISBbits.TRISB0 = 1;
    TRISBbits.TRISB1 = 1;
    TRISBbits.TRISB2 = 0;
    TRISBbits.TRISB3 = 0;
    TRISBbits.TRISB4 = 0;
    TRISBbits.TRISB5 = 0;
    TRISBbits.TRISB6 = 0;
    TRISBbits.TRISB7 = 0;

    INTCON2bits.RBPU = 1;

    LED_RED = 0;
    LED_GREEN = 0;
}

/* ------------------------------------------------------------------ */
/* Flow sensing                                                         */
/* ------------------------------------------------------------------ */
static FlowWindowResult Flow_CountWindow(void)
{
    FlowWindowResult result;
    uint8_t previous1, previous2, current1, current2;
    uint16_t ms, tick;

    result.count1 = 0u;
    result.count2 = 0u;
    result.diff = 0u;

    previous1 = FLOW1_PIN;
    previous2 = FLOW2_PIN;

    for (ms = 0u; ms < FLOW_WINDOW_MS; ms++)
    {
        for (tick = 0u; tick < 100u; tick++)
        {
            current1 = FLOW1_PIN;
            current2 = FLOW2_PIN;

            if (current1 && !previous1)
            {
                result.count1++;
                __delay_us(FLOW_DEBOUNCE_US);
                previous1 = FLOW1_PIN;
            }
            else
            {
                previous1 = current1;
            }

            if (current2 && !previous2)
            {
                result.count2++;
                __delay_us(FLOW_DEBOUNCE_US);
                previous2 = FLOW2_PIN;
            }
            else
            {
                previous2 = current2;
            }

            __delay_us(10);
        }
    }

    result.diff = (result.count1 > result.count2)
                      ? (uint16_t)(result.count1 - result.count2)
                      : (uint16_t)(result.count2 - result.count1);

    return result;
}

/* ------------------------------------------------------------------ */
/* Acoustic localisation                                                */
/* ------------------------------------------------------------------ */
static uint32_t Acoustic_MeasureEnergy(void)
{
    uint8_t i;
    int16_t sample;
    uint32_t energyA = 0u;
    uint32_t energyB = 0u;

    for (i = 0u; i < 16u; i++)
    {
        sample = (int16_t)ADC_Read(0u) - 512;
        energyA += (uint32_t)((int32_t)sample * (int32_t)sample);

        sample = (int16_t)ADC_Read(1u) - 512;
        energyB += (uint32_t)((int32_t)sample * (int32_t)sample);

        __delay_us(50);
    }

    return (energyA > energyB) ? energyA : energyB;
}

static void Acoustic_CaptureSamples(void)
{
    uint8_t i;

    for (i = 0u; i < SAMPLE_COUNT; i++)
    {
        g_micA[i] = (int16_t)ADC_Read(0u) - 512;
        g_micB[i] = (int16_t)ADC_Read(1u) - 512;
        __delay_us(INTER_SAMPLE_US);
    }
}

static int16_t Acoustic_FindBestLag(void)
{
    int8_t   lag;
    int8_t   best_lag   = 0;
    uint8_t  i;
    uint32_t best_score = 0u;
    uint32_t scores[2u * (uint8_t)MAX_LAG + 1u];

    for (lag = -(int8_t)MAX_LAG; lag <= (int8_t)MAX_LAG; lag++)
    {
        int32_t  sum     = 0;
        uint32_t energyA = 0u;
        uint32_t energyB = 0u;
        uint32_t score   = 0u;

        for (i = 0u; i < SAMPLE_COUNT; i++)
        {
            int16_t j = (int16_t)i + (int16_t)lag;
            if (j >= 0 && j < (int16_t)SAMPLE_COUNT)
            {
                int16_t a = g_micA[i];
                int16_t b = g_micB[j];
                sum     += (int32_t)a * (int32_t)b;
                energyA += (uint32_t)((int32_t)a * (int32_t)a);
                energyB += (uint32_t)((int32_t)b * (int32_t)b);
            }
        }

        if (sum > 0 && energyA > 0u && energyB > 0u)
        {
            uint64_t denominator = ((uint64_t)energyA * (uint64_t)energyB) >> 16;
            if (denominator == 0u) { denominator = 1u; }
            score = (uint32_t)(((uint64_t)(uint32_t)sum *
                                (uint64_t)(uint32_t)sum) / denominator);

            if (score > best_score)
            {
                best_score = score;
                best_lag   = lag;
            }
        }

        scores[(uint8_t)((int8_t)lag + (int8_t)MAX_LAG)] = score;
    }

    /* Parabolic interpolation ? refines lag to Q4 fixed-point (x16).
     * Uses the three scores around the integer peak to fit a parabola
     * and locate the true sub-sample maximum. */
    if (best_lag > -(int8_t)MAX_LAG && best_lag < (int8_t)MAX_LAG)
    {
        uint8_t idx    = (uint8_t)((int8_t)best_lag + (int8_t)MAX_LAG);
        int32_t y0     = (int32_t)scores[idx - 1u];
        int32_t y1     = (int32_t)scores[idx];
        int32_t y2     = (int32_t)scores[idx + 1u];
        int32_t denom  = y0 - 2L * y1 + y2;  /* always <= 0 at a maximum */

        if (denom != 0L)
        {
            /* delta = (y0 - y2) / (2 * denom), scaled x16 = 8*(y0-y2)/denom */
            int16_t delta_q4 = (int16_t)(8L * (y0 - y2) / denom);
            return (int16_t)((int16_t)best_lag * 16) + delta_q4;
        }
    }

    return (int16_t)((int16_t)best_lag * 16);
}

static uint16_t Acoustic_PositionFromLag(int16_t lag_q4)
{
    int32_t delay_us    = ((int32_t)lag_q4 * SAMPLE_PERIOD_US) / 16L + ADC_INTER_CH_BIAS_US;
    int32_t position_mm = (PIPE_LENGTH_MM * 1000L + SOUND_SPEED_MPS * delay_us) / 2000L;

    if (position_mm < 0L)
    {
        position_mm = 0L;
    }
    else if (position_mm > PIPE_LENGTH_MM)
    {
        position_mm = PIPE_LENGTH_MM;
    }

    return (uint16_t)position_mm;
}

static uint16_t Acoustic_Locate(uint16_t previous_position_mm)
{
    uint8_t run;
    int32_t lag_sum = 0;
    uint8_t valid_runs = 0u;
    int16_t lag_average;
    uint32_t energy;

    for (run = 0u; run < LAG_AVG_COUNT; run++)
    {
        UART_PrintTimestamp();
        UART_Print("SAMPLING... (run ");
        UART_PrintUInt((uint16_t)(run + 1u));
        UART_Write('/');
        UART_PrintUInt(LAG_AVG_COUNT);
        UART_Print(")\r\n");

        energy = Acoustic_MeasureEnergy();
        if (energy < ENERGY_THRESHOLD)
        {
            UART_Log("  (low energy - skipping run)");
            continue;
        }

        Acoustic_CaptureSamples();
        lag_sum += (int32_t)Acoustic_FindBestLag();
        valid_runs++;
    }

    if (valid_runs == 0u)
    {
        UART_Log("  WARNING: all runs low energy - holding last position");
        return previous_position_mm;
    }

    if (lag_sum >= 0)
        lag_average = (int16_t)((lag_sum + (int32_t)(valid_runs / 2u)) / (int32_t)valid_runs);
    else
        lag_average = (int16_t)((lag_sum - (int32_t)(valid_runs / 2u)) / (int32_t)valid_runs);

    UART_PrintTimestamp();
    UART_Print("AVG LAG=");
    if (lag_average < 0) { UART_Write('-'); UART_PrintUInt((uint16_t)((-lag_average) / 16)); }
    else                 {                  UART_PrintUInt((uint16_t)(  lag_average   / 16)); }
    UART_Print(" (");
    UART_PrintUInt(valid_runs);
    UART_Print(" valid runs)\r\n");

    return Acoustic_PositionFromLag(lag_average);
}

static uint16_t AbsDiffU16(uint16_t a, uint16_t b)
{
    return (a > b) ? (uint16_t)(a - b) : (uint16_t)(b - a);
}

/* ------------------------------------------------------------------ */
/* Startup banner                                                       */
/* ------------------------------------------------------------------ */
static void Startup(void)
{
    uint8_t i;

    LCD_SetCursor(0, 0);
    LCD_Print("  PIPE MONITOR  ");
    LCD_SetCursor(1, 0);
    LCD_Print("   SYSTEM v7.3  ");

    UART_Print("\r\n==============================\r\n");
    UART_Print("  AQUADETECTION v7.3\r\n");
    UART_Print("  Flow : RB0/RB1 + 10k pull-ups\r\n");
    UART_Print("  Mic  : AN0/AN1 (split capture)\r\n");
    UART_Print("  Xcorr: energy-normalised, N=32, MAX_LAG=10\r\n");
    UART_Print("  Pos  : calibrated, T=291us, v=338m/s\r\n");
    UART_Print("  MODE : Position always on LCD; localise in bg\r\n");
    UART_Print("==============================\r\n\r\n");
    __delay_ms(1500);

    LCD_SetCursor(0, 0);
    LCD_Print(" INITIALISING...");
    LCD_SetCursor(1, 0);
    LCD_Print("                ");
    UART_Log("INITIALISING HARDWARE...");
    __delay_ms(600);

    for (i = 0u; i < 3u; i++)
    {
        LED_GREEN = 1;
        __delay_ms(120);
        LED_GREEN = 0;
        __delay_ms(120);
    }

    LCD_SetCursor(0, 0);
    LCD_Print(" SYSTEM  READY! ");
    LCD_SetCursor(1, 0);
    LCD_Print("  MONITORING... ");
    UART_Log("SYSTEM READY - MONITORING STARTED");
    UART_Print("\r\n");

    LED_GREEN = 1;
    __delay_ms(500);
    LED_GREEN = 0;
}

/* ------------------------------------------------------------------ */
/* Main                                                                 */
/* ------------------------------------------------------------------ */
void main(void)
{
    FlowWindowResult flow;
    uint16_t new_pos_s1_mm;
    uint16_t new_pos_s2_mm;

    /*
     * g_shown_pos_s1_mm holds the last position written to the LCD.
     * It is initialised to 500 mm (pipe midpoint) so the first
     * acoustic run has a sensible fallback value.
     */
    g_shown_pos_s1_mm = 500u;

    IO_Init();
    UART_Init();
    ADC_Init();
    LCD_Init();
    Timer1_Init();
    Startup();

    /* Show "CHECKING FLOW" once at boot */
    LCD_ShowChecking();
    g_state = STATE_FLOW_CHECK;

    while (1)
    {
        /* Always service the timer flag first - no skipping */
        if (g_timer1_flag)
        {
            g_timer1_flag = 0;
            g_elapsed_sec++;
            if (g_elapsed_sec >= 6000u)
            {
                g_elapsed_sec = 0u;
            }
        }

        /* ---------------------------------------------------------- */
        /* STEP 1: Check flow every cycle regardless of state         */
        /* ---------------------------------------------------------- */
        UART_PrintTimestamp();
        UART_Print("CHECKING FLOW... (window=");
        UART_PrintUInt(FLOW_WINDOW_MS);
        UART_Print("ms)\r\n");

        flow = Flow_CountWindow();

        /* ---------------------------------------------------------- */
        /* STEP 2: Update state machine based on flow result          */
        /* ---------------------------------------------------------- */
        if (flow.diff < FLOW_DIFF_THRESHOLD)
        {
            /* ---- Flow is balanced - no leak signal ---- */
            g_leak_confirm = 0u;

            if (g_clear_confirm < FLOW_CONFIRM_COUNT)
            {
                g_clear_confirm++;
            }

            UART_PrintTimestamp();
            UART_Print("NO LEAK - C1=");
            UART_PrintUInt(flow.count1);
            UART_Print(" C2=");
            UART_PrintUInt(flow.count2);
            UART_Print(" DIFF=");
            UART_PrintUInt(flow.diff);
            UART_Print("\r\n");

            if (g_clear_confirm >= FLOW_CONFIRM_COUNT)
            {
                LED_GREEN = 1;
                LED_RED = 0;

                if (g_state != STATE_CLEAR)
                {
                    g_state = STATE_CLEAR;
                    g_shown_pos_s1_mm = 500u; /* Reset fallback position */
                    LCD_ShowNoLeak();
                    UART_Log("*** SYSTEM CLEAR - NO ACTIVE LEAK ***");
                }
            }
        }
        else
        {
            /* ---- Flow imbalance detected ---- */
            g_clear_confirm = 0u;
            LED_RED = 1;
            LED_GREEN = 0;

            if (g_leak_confirm < FLOW_CONFIRM_COUNT)
            {
                g_leak_confirm++;
            }

            UART_PrintTimestamp();
            UART_Print("*** LEAK DETECTED - C1=");
            UART_PrintUInt(flow.count1);
            UART_Print(" C2=");
            UART_PrintUInt(flow.count2);
            UART_Print(" DIFF=");
            UART_PrintUInt(flow.diff);
            UART_Print(" ***\r\n");

            if (g_leak_confirm < FLOW_CONFIRM_COUNT)
            {
                /* Still accumulating confirmation counts */
                UART_PrintTimestamp();
                UART_Print("CONFIRMING... (");
                UART_PrintUInt(g_leak_confirm);
                UART_Write('/');
                UART_PrintUInt(FLOW_CONFIRM_COUNT);
                UART_Print(")\r\n");

                if (g_state != STATE_LEAK_CONFIRM)
                {
                    g_state = STATE_LEAK_CONFIRM;
                    LCD_ShowLeakFound(); /* Only brief - next cycle runs location */
                }
            }
            else
            {
                /* -------------------------------------------------- */
                /* Leak confirmed.                                      */
                /*                                                      */
                /* Run acoustic localisation in the background.         */
                /* The LCD is updated ONLY if the result differs from   */
                /* the currently shown position by > POSITION_TOL_MM.  */
                /* The LCD is NEVER cleared to "CHECKING" or           */
                /* "LOCATING" once we are in STATE_POSITION.           */
                /* -------------------------------------------------- */
                UART_Log("LEAK CONFIRMED - RUNNING ACOUSTIC LOCALISATION");

                new_pos_s1_mm = Acoustic_Locate(g_shown_pos_s1_mm);
                new_pos_s2_mm = (uint16_t)(PIPE_LENGTH_MM - new_pos_s1_mm);

                UART_PrintTimestamp();
                UART_Print("RESULT: S1=");
                UART_PrintUInt(new_pos_s1_mm);
                UART_Print("mm  S2=");
                UART_PrintUInt(new_pos_s2_mm);
                UART_Print("mm\r\n");

                if (g_state != STATE_POSITION)
                {
                    /*
                     * First confirmed location reading - always show it
                     * and transition to STATE_POSITION.
                     */
                    g_state = STATE_POSITION;
                    g_shown_pos_s1_mm = new_pos_s1_mm;
                    LCD_ShowPosition(new_pos_s1_mm, new_pos_s2_mm);

                    UART_Log("POSITION DISPLAYED - NOW HOLDING ON LCD");
                }
                else
                {
                    /*
                     * Already showing a position.
                     * Only refresh the LCD if the position has moved
                     * significantly, otherwise leave the display alone.
                     */
                    if (AbsDiffU16(g_shown_pos_s1_mm, new_pos_s1_mm) > POSITION_TOL_MM)
                    {
                        g_shown_pos_s1_mm = new_pos_s1_mm;
                        LCD_ShowPosition(new_pos_s1_mm, new_pos_s2_mm);

                        UART_PrintTimestamp();
                        UART_Print("POSITION UPDATED ON LCD (delta > ");
                        UART_PrintUInt(POSITION_TOL_MM);
                        UART_Print("mm)\r\n");
                    }
                    else
                    {
                        UART_PrintTimestamp();
                        UART_Print("POSITION STABLE - LCD UNCHANGED (delta <= ");
                        UART_PrintUInt(POSITION_TOL_MM);
                        UART_Print("mm)\r\n");
                    }
                }

                UART_Log("BACKGROUND LOCALISATION COMPLETE - CONTINUING");
                UART_Print("\r\n");
            }
        }
    }
}