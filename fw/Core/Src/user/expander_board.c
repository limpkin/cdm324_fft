#include "user/expander_board.h"
#include "fatfs.h"
/* SPI to the sd card */
SPI_HandleTypeDef hspi3;
/* Variables to write to the SD card */
FATFS expander_board_fs;
FIL expander_board_file;


/*! \fn     expander_init(void)
*   \brief  Expander initialization code
*   \return TRUE if a SD card is detected
*/
BOOL expander_init(void)
{
	GPIO_InitTypeDef GPIO_InitStruct = {0};

	/* GPIO Ports Clock Enable */
	__HAL_RCC_GPIOA_CLK_ENABLE();
	__HAL_RCC_GPIOB_CLK_ENABLE();

	/* Configure GPIO pins: SD card detect */
	GPIO_InitStruct.Pin = SD_CD_Pin;
	GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
	GPIO_InitStruct.Pull = GPIO_PULLUP;
	HAL_GPIO_Init(SD_CD_Pin_Port, &GPIO_InitStruct);

	/* Configure GPIO pins: user switch */
	GPIO_InitStruct.Pin = SWITCH_Pin;
	GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
	GPIO_InitStruct.Pull = GPIO_PULLUP;
	HAL_GPIO_Init(SWITCH_GPIO_Port, &GPIO_InitStruct);

	/* Configure GPIO pins: SPI slave select */
	GPIO_InitStruct.Pin = SPI_SS_Pin;
	GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_MEDIUM;
	HAL_GPIO_Init(SPI_SS_GPIO_Port, &GPIO_InitStruct);

	/* Configure SPI pins */
	GPIO_InitStruct.Pin = GPIO_PIN_3|GPIO_PIN_4|GPIO_PIN_5;
	GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_MEDIUM;
	GPIO_InitStruct.Alternate = GPIO_AF6_SPI3;
	HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

	/* SPI3 parameter configuration */
	hspi3.Instance = SPI3;
	hspi3.Init.Mode = SPI_MODE_MASTER;
	hspi3.Init.Direction = SPI_DIRECTION_2LINES;
	hspi3.Init.DataSize = SPI_DATASIZE_8BIT;
	hspi3.Init.CLKPolarity = SPI_POLARITY_LOW;
	hspi3.Init.CLKPhase = SPI_PHASE_1EDGE;
	hspi3.Init.NSS = SPI_NSS_SOFT;
	hspi3.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_16;
	hspi3.Init.FirstBit = SPI_FIRSTBIT_MSB;
	hspi3.Init.TIMode = SPI_TIMODE_DISABLE;
	hspi3.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
	hspi3.Init.CRCPolynomial = 7;
	hspi3.Init.CRCLength = SPI_CRC_LENGTH_DATASIZE;
	hspi3.Init.NSSPMode = SPI_NSS_PULSE_DISABLE;
	HAL_SPI_Init(&hspi3);

	/* FatFS library init */
	MX_FATFS_Init();

	/* uSD card inserted? */
	if (HAL_GPIO_ReadPin(SD_CD_Pin_Port, SD_CD_Pin) == GPIO_PIN_RESET)
	{
		/* Mount filesystem */
		f_mount(&expander_board_fs, "", 0);

		/* Test code */
		/*f_open(&expander_board_file, "test.txt", FA_OPEN_ALWAYS | FA_WRITE | FA_READ);
		f_lseek(&expander_board_file, expander_board_file.fsize);
		f_puts("This is an example text to check SD Card Module with STM32 Blue Pill\n", &expander_board_file);
		f_close(&expander_board_file);*/

		/* Return success */
		return TRUE;
	}

	/* No uSD card */
	return FALSE;
}

/*! \fn     expander_is_kph_selected(void)
*   \brief  Check if KPH is selected
*   \return TRUE if so
*/
BOOL expander_is_kph_selected(void)
{
	if (HAL_GPIO_ReadPin(SWITCH_GPIO_Port, SWITCH_Pin) == GPIO_PIN_RESET)
	{
		return TRUE;
	}
	return FALSE;
}
