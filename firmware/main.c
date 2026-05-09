/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* ── LIMA Paket Sabitleri ── */
#define LIMA_START_BYTE   0xAA
#define LIMA_END_BYTE     0x55
#define LIMA_PACKET_SIZE  8
#define CMD_STOP 0x01  // Python logunda STOP genellikle 0x01 veya 0x00 gelir, kontrol et

/* ── Sistem & Bağlantı ── */
#define CMD_YP            0xF2
#define CMD_COMCHECK      0x02
#define CMD_TESTMODE      0x03

/* ── Süreç / Hizalama / Işık ── */
#define CMD_AUTOALIGN     0xC5
#define CMD_AUTOFOCUS     0xC6
#define CMD_ALIGNCHK      0xC2
#define CMD_ALIGNCHKBACK  0xC3
#define CMD_EXPOSURE      0xD0
#define CMD_CONTMODE      0xB0

/* ── Pnömatik / Valf ── */
#define CMD_MASKVSEL      0xE3
#define CMD_SAMPHVSEL     0xE5
#define CMD_SAMPFVSEL     0xE6
#define CMD_WECLSEL       0xE8
#define CMD_CONVSEL       0xE2
#define CMD_OPTICSEL      0xE9
#define CMD_RINGSEL       0xE7

/* ── Motor / Homing ── */
#define CMD_HOMESX        0x66
#define CMD_HOMESY        0x76
#define CMD_HOMESZ        0x84
#define CMD_HOMESTH       0x94
#define CMD_HOMEMLX       0x53
#define CMD_HOMEMRZ       0x19
#define CMD_MOVEMLZ       0x10
#define CMD_GOSXY         0x78

/* ── RX Yanıt CMD'leri (Pozisyon & Home OK bildirimleri) ── */
#define CMD_HOMESXOK      0x67   /* HOMESX onay */
#define CMD_HOMESYOK      0x77   /* HOMESY onay */
#define CMD_HOMESZOK      0x85   /* HOMESZ onay */
#define CMD_HOMESTHOK     0x95   /* HOMESTH onay */
#define CMD_HOMEMLXOK     0x54   /* HOMEMLX onay */
#define CMD_HOMEMRZOK     0x1A   /* HOMEMRZ onay */
#define CMD_MLZPOS        0x11   /* MOVEMLZ pozisyon bildirimi */
#define CMD_SXMPOS        0x79   /* GOSXY → X pozisyon bildirimi */
#define CMD_SYMPOS        0x7A   /* GOSXY → Y pozisyon bildirimi */


// 1. Microscope Left (MLX, MLY, MLZ)
#define CMD_MLXPOS        0xA0
#define CMD_MLYPOS        0xA1
#define CMD_MLXMPOS       0xA2
#define CMD_MLXGPOS       0xA3 // (Hata 1: 0x53 idi, değişti)
#define CMD_MLYMPOS       0xA4
#define CMD_MLYGPOS       0xA5
#define CMD_MLXP          0xA6
#define CMD_MLXN          0xA7
#define CMD_MLYP          0xA8
#define CMD_MLYN          0xA9
#define CMD_GOMLZ         0xAB
#define CMD_MLZP          0xAC
#define CMD_MLZN          0xAD

// 2. Microscope Right
#define CMD_MRXPOS        0xB1 // (0xB0 rezerve idi, kaydırdık)
#define CMD_MRYPOS        0xB2
#define CMD_MRZPOS        0xB3
#define CMD_MRXMPOS       0xB4
#define CMD_MRXGPOS       0xB5
#define CMD_MRYMPOS       0xB6
#define CMD_MRYGPOS       0xB7
#define CMD_MRXP          0xB8
#define CMD_MRXN          0xB9
#define CMD_MRYP          0xBA
#define CMD_MRYN          0xBB
#define CMD_MOVEMRZ       0xBC
#define CMD_GOMRZ         0xBD
#define CMD_MRZP          0xBE
#define CMD_MRZN          0xBF

// 3. Sample X/Y/Z (Homing 0x76-0x79 ve 0x78 arasını kullanma)
#define CMD_SXPOS         0x30
#define CMD_SYPOS         0x31
#define CMD_SZPOS         0x32
#define CMD_SXGPOS        0x33
#define CMD_SYGPOS        0x34
#define CMD_SXP           0x35
#define CMD_SXN           0x36 // (Hata 2: 0x76 idi, değişti)
#define CMD_SYP           0x37
#define CMD_SYN           0x38 // (Hata 4: 0x78 idi, değişti)
#define CMD_MOVESZ        0x39
#define CMD_GOSZ          0x3A
#define CMD_SZP           0x3B
#define CMD_SZN           0x3C

// 4. Theta (Homing 0x94-0x95 arasını kullanma)
#define CMD_STPOS         0x20
#define CMD_MOVESTH       0x21
#define CMD_GOSTH         0x22
#define CMD_STHP          0x23
#define CMD_STHN          0x24 // (Hata 3: 0x94 idi, değişti)
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
TIM_HandleTypeDef htim2;

UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
volatile uint8_t rx_byte;               // Tekil okunan byte];
volatile uint8_t rx_buffer[LIMA_PACKET_SIZE]; // Paket tamponu
volatile uint8_t rx_index = 0;             // Tampon indeksi
volatile uint8_t packet_ready = 0;  // Paket hazır bayrağı

volatile int8_t move_dir_MLY = 0; // 'volatile' eklemek şart!
volatile int8_t move_dir_SZ  = 0;
volatile int32_t pos_MLY = 0;
volatile int32_t pos_SZ  = 0;

int32_t pos_MLX = 0;
int8_t move_dir_MLX = 0;


int32_t pos_MLZ = 0;
int8_t move_dir_MLZ = 0;

int32_t pos_MRX = 0;
int8_t move_dir_MRX = 0;

int32_t pos_MRY = 0;
int8_t move_dir_MRY = 0;

int32_t pos_MRZ = 0;
int8_t move_dir_MRZ = 0;

int32_t pos_SX  = 0;
int8_t move_dir_SX  = 0;

int32_t pos_SY  = 0;
int8_t move_dir_SY  = 0;


int32_t pos_STH = 0; // Theta (Açısal)
int8_t move_dir_STH = 0;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_TIM2_Init(void);
static void MX_USART2_UART_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* ── Lima_SendPacket: mevcut fonksiyon (değişmedi) ── */
void Lima_SendPacket(uint8_t cmd, uint32_t value)
{
    uint8_t tx_buffer[LIMA_PACKET_SIZE];
    tx_buffer[0] = LIMA_START_BYTE;
    tx_buffer[1] = cmd;
    tx_buffer[2] = (value >> 24) & 0xFF;
    tx_buffer[3] = (value >> 16) & 0xFF;
    tx_buffer[4] = (value >>  8) & 0xFF;
    tx_buffer[5] =  value        & 0xFF;
    tx_buffer[6] = (tx_buffer[1] + tx_buffer[2] + tx_buffer[3]
                  + tx_buffer[4] + tx_buffer[5]) & 0xFF;
    tx_buffer[7] = LIMA_END_BYTE;
    HAL_UART_Transmit(&huart2, tx_buffer, LIMA_PACKET_SIZE, 100);
}

void Move_Axis_Simulated(volatile int32_t *current_pos, int32_t value, uint8_t feedback_cmd, uint8_t is_relative)
{
    int32_t target_pos;

    if (is_relative) target_pos = *current_pos + value;
    else             target_pos = value;

    int direction = (target_pos > *current_pos) ? 1 : -1;

    while (*current_pos != target_pos) {
        *current_pos += direction;

        Lima_SendPacket(feedback_cmd, *current_pos);
        HAL_Delay(10);
    }
}

/*
 * ── Valf Kontrol Yardımcısı ──────────────────────────────────────────────────
 * Gelen data=1 → GPIO HIGH (valf aç), data=0 → GPIO LOW (kapat).
 * GPIO okuma ile gerçek durumu teyit edip yanıt döner.
 *
 * Kullanım: Lima_ValveControl(CMD_MASKVSEL, data, MASKVAC_GPIO_Port, MASKVAC_Pin);
 *
 * NOT: GPIO port/pin tanımlarını kendi CubeMX .ioc dosyanıza göre
 *       main.h içinde tanımlamanız gerekir.
 * ─────────────────────────────────────────────────────────────────────────────
 */
static void Lima_ValveControl(uint8_t response_cmd,
                               uint32_t data,
                               GPIO_TypeDef *GPIOx,
                               uint16_t GPIO_Pin)
{
    /* Komutu uygula */
    HAL_GPIO_WritePin(GPIOx, GPIO_Pin, (data == 1) ? GPIO_PIN_SET : GPIO_PIN_RESET);

    /* Kısa bekleme – valfin mekanik tepkisi için (donanıma göre ayarlayın) */
    HAL_Delay(10);

    /* Gerçek pin durumunu oku ve yanıt olarak gönder */
    uint32_t actual_state = (HAL_GPIO_ReadPin(GPIOx, GPIO_Pin) == GPIO_PIN_SET) ? 1 : 0;
    Lima_SendPacket(response_cmd, actual_state);
}

/*
 * ── Homing Yardımcısı ────────────────────────────────────────────────────────
 * Motoru sürer, limit switch tetiklendiğinde OK paketi yollar.
 *
 * GERÇEK UYGULAMA İÇİN: Bu fonksiyonu step/dir GPIO veya STEP-MOTOR
 * kütüphanenizle doldurun. Şu an blocking-poll örneği gösterilmiştir;
 * üretim kodunda interrupt/timer tabanlı geçiş önerilir.
 * ─────────────────────────────────────────────────────────────────────────────
 */
static void Lima_DoHoming(uint8_t ok_cmd,
                          GPIO_TypeDef *LimitSW_Port,
                          uint16_t     LimitSW_Pin)
{
    /*
     * TODO: Motoru negatif yönde sür.
     * Örnek: Motor_Start(AXIS_X, DIR_NEGATIVE);
     */

    /* Limit switch aktif olana kadar bekle (active-low varsayımı) */
    uint32_t timeout = HAL_GetTick() + 10000; /* 10 sn max */
    while (HAL_GPIO_ReadPin(LimitSW_Port, LimitSW_Pin) != GPIO_PIN_RESET)
    {
        if (HAL_GetTick() > timeout)
        {
            /* Zaman aşımı → data=0 ile hata bildir */
            Lima_SendPacket(ok_cmd, 0);
            return;
        }
    }

    /*
     * TODO: Motoru durdur.
     * Örnek: Motor_Stop(AXIS_X);
     */

    /* Başarılı home → data=1 */
    Lima_SendPacket(ok_cmd, 1);
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_TIM2_Init();
  MX_USART2_UART_Init();
  /* USER CODE BEGIN 2 */

  // İlk byte için interrupt'ı başlat
  	  HAL_UART_Receive_IT(&huart2, (uint8_t *)&rx_byte, 1);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  	while (1)
  	{
  		/* ====================================================================
  		     * 1. SÜREKLİ HAREKET (JOG) KONTROLÜ
  		     * DİKKAT: Bu blok packet_ready dışında olmalıdır ki sayılar sürekli aksın!
  		     * ==================================================================== */

  		    // --- MLY Eksen Hareketi ---
  		    if (move_dir_MLY != 0) {
  		        pos_MLY += move_dir_MLY;
  		        // Python'daki bufferMLYPOS kutusunu günceller
  		        Lima_SendPacket(CMD_MLYPOS, pos_MLY);
  		        HAL_Delay(20); // Hareket hızı ve UI akış hızı
  		    }

  		    // --- SZ Eksen Hareketi ---
  		    if (move_dir_SZ != 0) {
  		        pos_SZ += move_dir_SZ;
  		        // Python'daki bufferSZPOS kutusunu günceller
  		        Lima_SendPacket(CMD_SZPOS, pos_SZ);
  		        HAL_Delay(20);
  		    }


  		    /* ====================================================================
  		     * 2. PAKET OKUMA VE KOMUT İŞLEME
  		     * ==================================================================== */
  		    if (packet_ready)
  		    {
  		        packet_ready = 0;

  		        // Değişkenleri burada tanımlıyoruz ki scope (kapsam) hatası vermesin
  		        uint8_t  cmd      = rx_buffer[1];
  		        uint32_t data     = ((uint32_t)rx_buffer[2] << 24)
  		                          | ((uint32_t)rx_buffer[3] << 16)
  		                          | ((uint32_t)rx_buffer[4] <<  8)
  		                          |  (uint32_t)rx_buffer[5];
  		        uint8_t  checksum = rx_buffer[6];

  		        /* ── Checksum Doğrulama ── */
  		        uint8_t calc_chk = (cmd
  		                          + rx_buffer[2] + rx_buffer[3]
  		                          + rx_buffer[4] + rx_buffer[5]) & 0xFF;

  		        if (calc_chk != checksum) goto next_packet; /* Bozuk paket, yoksay */

  		        /* ════════════════════════════════════════════════════════════════════
  		         * LIMA KOMUT İŞLEME — switch(cmd)
  		         * ════════════════════════════════════════════════════════════════════ */
  		        switch (cmd)
  		        {
  		            /* ── 1. SİSTEM & BAĞLANTI ──────────────────────────────────── */
  		            case CMD_YP:
  		                Lima_SendPacket(CMD_YP, 1);
  		                break;

  		            case CMD_COMCHECK:
  		                Lima_SendPacket(CMD_COMCHECK, data);
  		                break;

  		            case CMD_TESTMODE:
  		                Lima_SendPacket(CMD_TESTMODE, data);
  		                break;

  		            /* ── 2. SÜREÇ / HİZALAMA / IŞIK ───────────────────────────── */
  		            case CMD_AUTOALIGN:
  		                Lima_SendPacket(CMD_AUTOALIGN, data);
  		                break;

  		            case CMD_AUTOFOCUS:
  		                Lima_SendPacket(CMD_AUTOFOCUS, data);
  		                break;

  		            case CMD_ALIGNCHK:
  		                Lima_SendPacket(CMD_ALIGNCHK, data);
  		                break;

  		            case CMD_ALIGNCHKBACK:
  		                Lima_SendPacket(CMD_ALIGNCHKBACK, 3);
  		                HAL_Delay(500);
  		                Lima_SendPacket(CMD_ALIGNCHKBACK, 0);
  		                break;

  		            case CMD_EXPOSURE:
  		                HAL_GPIO_WritePin(EXPOSURE_GPIO_Port, EXPOSURE_Pin,
  		                                  (data == 1) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  		                Lima_SendPacket(CMD_EXPOSURE, data);
  		                break;

  		            case CMD_CONTMODE:
  		                Lima_SendPacket(CMD_CONTMODE, data);
  		                break;

  		            /* ── 3. PNÖMATİK / VALF ────────────────────────────────────── */
  		            case CMD_MASKVSEL:
  		                Lima_ValveControl(CMD_MASKVSEL, data, MASKVAC_GPIO_Port, MASKVAC_Pin);
  		                break;

  		            case CMD_SAMPHVSEL:
  		                Lima_ValveControl(CMD_SAMPHVSEL, data, SAMPHVAC_GPIO_Port, SAMPHVAC_Pin);
  		                break;

  		            case CMD_SAMPFVSEL:
  		                Lima_ValveControl(CMD_SAMPFVSEL, data, SAMPFVAC_GPIO_Port, SAMPFVAC_Pin);
  		                break;

  		            case CMD_WECLSEL:
  		                Lima_ValveControl(CMD_WECLSEL, data, WECLOCK_GPIO_Port, WECLOCK_Pin);
  		                break;

  		            case CMD_CONVSEL:
  		                Lima_ValveControl(CMD_CONVSEL, data, CONTVAC_GPIO_Port, CONTVAC_Pin);
  		                break;

  		            case CMD_OPTICSEL:
  		                Lima_ValveControl(CMD_OPTICSEL, data, OPTIVAC_GPIO_Port, OPTIVAC_Pin);
  		                break;

  		            /* ── 4. MOTOR / HOMİNG ─────────────────────────────────────── */
  		            case CMD_HOMESX:
  		                Lima_DoHoming(CMD_HOMESXOK, LMSW_SX_GPIO_Port, LMSW_SX_Pin);
  		                break;

  		            case CMD_HOMESY:
  		                Lima_DoHoming(CMD_HOMESYOK, LMSW_SY_GPIO_Port, LMSW_SY_Pin);
  		                break;

  		            case CMD_HOMESZ:
  		                Lima_DoHoming(CMD_HOMESZOK, LMSW_SZ_GPIO_Port, LMSW_SZ_Pin);
  		                break;

  		            case CMD_HOMESTH:
  		                Lima_DoHoming(CMD_HOMESTHOK, LMSW_TH_GPIO_Port, LMSW_TH_Pin);
  		                break;

  		            case CMD_HOMEMLX:
  		                Lima_DoHoming(CMD_HOMEMLXOK, LMSW_MLX_GPIO_Port, LMSW_MLX_Pin);
  		                break;

  		            case CMD_HOMEMRZ:
  		                Lima_DoHoming(CMD_HOMEMRZOK, LMSW_MRZ_GPIO_Port, LMSW_MRZ_Pin);
  		                break;

  		            /* ── 5. EKSEN KONTROLLERİ ───────────────────────────────────── */
  		            case CMD_MLXMPOS:
  		            case CMD_MLXGPOS:
  		                Move_Axis_Simulated(&pos_MLX, data, CMD_MLXPOS, 0);
  		                break;

  		            case CMD_MLYMPOS:
  		            case CMD_MLYGPOS:
  		                Move_Axis_Simulated(&pos_MLY, data, CMD_MLYPOS, 0);
  		                break;

  		            // MLX Jog Modu (+1 / -1)
  		            case CMD_MLXP:
  		                Move_Axis_Simulated(&pos_MLX,  1, CMD_MLXPOS, 1);
  		                break;
  		            case CMD_MLXN:
  		                Move_Axis_Simulated(&pos_MLX, -1, CMD_MLXPOS, 1);
  		                break;

  		            // MLY Jog Modu (Sürekli Akış Bayrakları)
  		            case CMD_MLYP:
  		                move_dir_MLY = 1;
  		                Lima_SendPacket(CMD_MLYP, 1);
  		                break;
  		            case CMD_MLYN:
  		                move_dir_MLY = -1;
  		                break;

  		            /* ---------------------------------------------------
  		             * MICROSCOPE RIGHT (MRX ve MRY)
  		             * --------------------------------------------------- */
  		            case CMD_MRXMPOS:
  		            case CMD_MRXGPOS:
  		                Move_Axis_Simulated(&pos_MRX, data, CMD_MRXPOS, 0);
  		                break;

  		            case CMD_MRYMPOS:
  		            case CMD_MRYGPOS:
  		                Move_Axis_Simulated(&pos_MRY, data, CMD_MRYPOS, 0);
  		                break;

  		            case CMD_MRXP: Move_Axis_Simulated(&pos_MRX,  1, CMD_MRXPOS, 1); break;
  		            case CMD_MRXN: Move_Axis_Simulated(&pos_MRX, -1, CMD_MRXPOS, 1); break;
  		            case CMD_MRYP: Move_Axis_Simulated(&pos_MRY,  1, CMD_MRYPOS, 1); break;
  		            case CMD_MRYN: Move_Axis_Simulated(&pos_MRY, -1, CMD_MRYPOS, 1); break;

  		            /* ---------------------------------------------------
  		             * MICROSCOPE LEFT ZED (MLZ)
  		             * --------------------------------------------------- */
  		            case CMD_MOVEMLZ:
  		            case CMD_GOMLZ:
  		                Move_Axis_Simulated(&pos_MLZ, data, CMD_MLZPOS, 0);
  		                break;

  		            case CMD_MLZP: Move_Axis_Simulated(&pos_MLZ,  1, CMD_MLZPOS, 1); break;
  		            case CMD_MLZN: Move_Axis_Simulated(&pos_MLZ, -1, CMD_MLZPOS, 1); break;

  		            /* ---------------------------------------------------
  		             * MICROSCOPE RIGHT ZED (MRZ)
  		             * --------------------------------------------------- */
  		            case CMD_MOVEMRZ:
  		            case CMD_GOMRZ:
  		                Move_Axis_Simulated(&pos_MRZ, data, CMD_MRZPOS, 0);
  		                break;

  		            case CMD_MRZP: Move_Axis_Simulated(&pos_MRZ,  1, CMD_MRZPOS, 1); break;
  		            case CMD_MRZN: Move_Axis_Simulated(&pos_MRZ, -1, CMD_MRZPOS, 1); break;

  		            /* ---------------------------------------------------
  		             * SAMPLE X/Y (SX ve SY)
  		             * --------------------------------------------------- */
  		            case CMD_SXMPOS:
  		            case CMD_SXGPOS:
  		                Move_Axis_Simulated(&pos_SX, data, CMD_SXPOS, 0);
  		                break;

  		            case CMD_SYMPOS:
  		            case CMD_SYGPOS:
  		                Move_Axis_Simulated(&pos_SY, data, CMD_SYPOS, 0);
  		                break;

  		            case CMD_SXP: Move_Axis_Simulated(&pos_SX,  1, CMD_SXPOS, 1); break;
  		            case CMD_SXN: Move_Axis_Simulated(&pos_SX, -1, CMD_SXPOS, 1); break;
  		            case CMD_SYP: Move_Axis_Simulated(&pos_SY,  1, CMD_SYPOS, 1); break;
  		            case CMD_SYN: Move_Axis_Simulated(&pos_SY, -1, CMD_SYPOS, 1); break;

  		            case CMD_GOSXY:
  		                {
  		                    uint32_t sx_pos = data;
  		                    uint32_t sy_pos = data;
  		                    Lima_SendPacket(CMD_SXMPOS, sx_pos);
  		                    Lima_SendPacket(CMD_SYMPOS, sy_pos);
  		                }
  		                break;

  		            /* ---------------------------------------------------
  		             * ZED (SZ)
  		             * --------------------------------------------------- */
  		            case CMD_MOVESZ:
  		            case CMD_GOSZ:
  		                Move_Axis_Simulated(&pos_SZ, data, CMD_SZPOS, 0);
  		                break;

  		            // SZ Jog Modu (Sürekli Akış Bayrakları)
  		            case CMD_SZP:
  		                move_dir_SZ = 1;
  		                break;
  		            case CMD_SZN:
  		                move_dir_SZ = -1;
  		                break;

  		            /* ---------------------------------------------------
  		             * THETA (STH) - Açısal
  		             * --------------------------------------------------- */
  		            case CMD_MOVESTH:
  		            case CMD_GOSTH:
  		                Move_Axis_Simulated(&pos_STH, data, CMD_STPOS, 0);
  		                break;

  		            case CMD_STHP: Move_Axis_Simulated(&pos_STH,  1, CMD_STPOS, 1); break;
  		            case CMD_STHN: Move_Axis_Simulated(&pos_STH, -1, CMD_STPOS, 1); break;

  		            /* ── DURDURMA KOMUTU ────────────────────────────────────────── */
  		            case CMD_STOP:
  		                move_dir_MLY = 0;
  		                move_dir_SZ  = 0;
  		                Lima_SendPacket(CMD_STOP, 1);
  		                // Diğer eksenlerin bayraklarını da eklersen buraya 0 olarak yaz.
  		                break;

  		            /* ── Bilinmeyen Komut ───────────────────────────────────────── */
  		            default:
  		                // Tanımlanamayan veya Listede Olmayan Komutları Python'a Geri Yolla (Sniffer)
  		                Lima_SendPacket(cmd, data);
  		                break;

  		        } /* switch(cmd) */

  		        next_packet:; /* checksum hatası buraya atlar */

  		    } /* if(packet_ready) SONU */

  		}

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{

  /* USER CODE BEGIN TIM2_Init 0 */

  /* USER CODE END TIM2_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM2_Init 1 */

  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 16 -1;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 0xFFFF;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */

  /* USER CODE END TIM2_Init 2 */
  HAL_TIM_MspPostInit(&htim2);

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 9600;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, Buzzer_Pin|TRIG_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOD, EXPOSURE_Pin|OPTIVAC_Pin|CONTVAC_Pin|WECLOCK_Pin
                          |SAMPFVAC_Pin|SAMPHVAC_Pin|MASKVAC_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : Buzzer_Pin TRIG_Pin */
  GPIO_InitStruct.Pin = Buzzer_Pin|TRIG_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pin : LMSW_MRZ_Pin */
  GPIO_InitStruct.Pin = LMSW_MRZ_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(LMSW_MRZ_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : LMSW_MLX_Pin */
  GPIO_InitStruct.Pin = LMSW_MLX_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(LMSW_MLX_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : LMSW_TH_Pin */
  GPIO_InitStruct.Pin = LMSW_TH_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(LMSW_TH_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : EXPOSURE_Pin OPTIVAC_Pin CONTVAC_Pin WECLOCK_Pin
                           SAMPFVAC_Pin SAMPHVAC_Pin MASKVAC_Pin */
  GPIO_InitStruct.Pin = EXPOSURE_Pin|OPTIVAC_Pin|CONTVAC_Pin|WECLOCK_Pin
                          |SAMPFVAC_Pin|SAMPHVAC_Pin|MASKVAC_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  /*Configure GPIO pins : LMSW_SZ_Pin LMSW_SY_Pin LMSW_SX_Pin */
  GPIO_InitStruct.Pin = LMSW_SZ_Pin|LMSW_SY_Pin|LMSW_SX_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : PA9 PA10 */
  GPIO_InitStruct.Pin = GPIO_PIN_9|GPIO_PIN_10;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF7_USART1;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2)
    {
        // State Machine: Start Byte bekliyoruz
        if (rx_index == 0)
        {
            if (rx_byte == LIMA_START_BYTE)
            {
                rx_buffer[rx_index++] = rx_byte;
            }
        }
        else
        {
            // Start byte gelmiş, paketi doldurmaya devam et
            rx_buffer[rx_index++] = rx_byte;

            // Paket tamamlandı mı? (8 Byte)
            if (rx_index >= LIMA_PACKET_SIZE)
            {
                if (rx_buffer[LIMA_PACKET_SIZE - 1] == LIMA_END_BYTE)
                {
                    packet_ready = 1; // while döngüsünde işlenmesi için bayrak kaldır
                }
                rx_index = 0; // Bir sonraki paket için indeksi sıfırla
            }
        }

        // Bir sonraki byte için kesmeyi tekrar kur
        HAL_UART_Receive_IT(&huart2, (uint8_t *)&rx_byte, 1);    }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
