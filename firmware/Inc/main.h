/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f4xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define Buzzer_Pin GPIO_PIN_6
#define Buzzer_GPIO_Port GPIOA
#define MOTOR_IN1_Pin GPIO_PIN_7
#define MOTOR_IN1_GPIO_Port GPIOE
#define MOTOR_IN2_Pin GPIO_PIN_8
#define MOTOR_IN2_GPIO_Port GPIOE
#define MOTOR_IN3_Pin GPIO_PIN_9
#define MOTOR_IN3_GPIO_Port GPIOE
#define MOTOR_IN4_Pin GPIO_PIN_10
#define MOTOR_IN4_GPIO_Port GPIOE
#define LMSW_MRZ_Pin GPIO_PIN_14
#define LMSW_MRZ_GPIO_Port GPIOB
#define LMSW_MLX_Pin GPIO_PIN_15
#define LMSW_MLX_GPIO_Port GPIOB
#define LMSW_TH_Pin GPIO_PIN_8
#define LMSW_TH_GPIO_Port GPIOD
#define EXPOSURE_Pin GPIO_PIN_9
#define EXPOSURE_GPIO_Port GPIOD
#define OPTIVAC_Pin GPIO_PIN_10
#define OPTIVAC_GPIO_Port GPIOD
#define CONTVAC_Pin GPIO_PIN_11
#define CONTVAC_GPIO_Port GPIOD
#define WECLOCK_Pin GPIO_PIN_12
#define WECLOCK_GPIO_Port GPIOD
#define SAMPFVAC_Pin GPIO_PIN_13
#define SAMPFVAC_GPIO_Port GPIOD
#define SAMPHVAC_Pin GPIO_PIN_14
#define SAMPHVAC_GPIO_Port GPIOD
#define MASKVAC_Pin GPIO_PIN_15
#define MASKVAC_GPIO_Port GPIOD
#define LMSW_SZ_Pin GPIO_PIN_6
#define LMSW_SZ_GPIO_Port GPIOC
#define LMSW_SY_Pin GPIO_PIN_7
#define LMSW_SY_GPIO_Port GPIOC
#define LMSW_SX_Pin GPIO_PIN_8
#define LMSW_SX_GPIO_Port GPIOC
#define TRIG_Pin GPIO_PIN_8
#define TRIG_GPIO_Port GPIOA

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
