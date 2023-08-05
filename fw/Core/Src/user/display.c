#include "user/ascii_lib.h"
#include "user/display.h"
#include <string.h>
#include <stdio.h>
/* I2C to the LCD controller */
I2C_HandleTypeDef hi2c1;


/*! \fn     display_init(void)
*   \brief  Display initialization code
*   \return	Initialization result
*/
BOOL display_init(void)
{
	GPIO_InitTypeDef GPIO_InitStruct = {0};

	/* GPIO Ports Clock Enable */
	__HAL_RCC_GPIOB_CLK_ENABLE();

	/* Configure GPIO pins */
	GPIO_InitStruct.Pin = GPIO_PIN_6|GPIO_PIN_7;
	GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
	GPIO_InitStruct.Alternate = GPIO_AF4_I2C1;
	HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

	/* I2C1 parameter configuration */
	hi2c1.Instance = I2C1;
	hi2c1.Init.Timing = 0x0000020B;
	hi2c1.Init.OwnAddress1 = 0;
	hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
	hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
	hi2c1.Init.OwnAddress2 = 0;
	hi2c1.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
	hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
	hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
	HAL_I2C_Init(&hi2c1);
	HAL_I2CEx_ConfigAnalogFilter(&hi2c1, I2C_ANALOGFILTER_ENABLE);
	HAL_I2CEx_ConfigDigitalFilter(&hi2c1, 0);

	/* Ping the controller */
	if (HAL_I2C_IsDeviceReady(&hi2c1, DISPLAY_I2C_ADDR, 1, 10) == HAL_OK)
	{
		/* Software reset the controller */
		uint8_t reset_reg[] = {0b00101100};
		HAL_I2C_Mem_Write(&hi2c1, DISPLAY_I2C_ADDR, 0x00, I2C_MEMADD_SIZE_8BIT, reset_reg, 1, HAL_MAX_DELAY);
		reset_reg[0] = 0x00;
		HAL_I2C_Mem_Write(&hi2c1, DISPLAY_I2C_ADDR, 0x00, I2C_MEMADD_SIZE_8BIT, reset_reg, 1, HAL_MAX_DELAY);

		/* Configure the controller: 1/4 duty, 1/3 bias */
		uint8_t disp_ctrl_1[] = {0x01};
		HAL_I2C_Mem_Write(&hi2c1, DISPLAY_I2C_ADDR, 0x02, I2C_MEMADD_SIZE_8BIT, disp_ctrl_1, 1, HAL_MAX_DELAY);
		return TRUE;
	}
	else
	{
		return FALSE;
	}
}

/*! \fn     display_animation_step(uint16_t anim_step)
*   \brief  Display animation step
*   \param	anim_step	Animation step
*/
void display_animation_step(uint16_t anim_step)
{
	uint8_t com_reg_contents[4][3];
	memset(com_reg_contents, 0x00, sizeof(com_reg_contents));

	switch (anim_step)
	{
		case 0: com_reg_contents[0][0] = 1 << 4; break;
		case 1: com_reg_contents[0][1] = 1 << 4; break;
		case 2: com_reg_contents[0][1] = 1 << 6; break;
		case 3: com_reg_contents[0][2] = 1 << 0; break;
		case 4: com_reg_contents[0][2] = 1 << 1; break;
		case 5: com_reg_contents[2][2] = 1 << 1; break;
		case 6: com_reg_contents[3][2] = 1 << 1; break;
		case 7: com_reg_contents[3][1] = 1 << 7; break;
		case 8: com_reg_contents[3][1] = 1 << 5; break;
		case 9: com_reg_contents[3][1] = 1 << 3; break;
		case 10: com_reg_contents[2][0] = 1 << 4; break;
		case 11: com_reg_contents[1][0] = 1 << 4; break;
		default: break;
	}

	/* Update whole display */
	HAL_I2C_Mem_Write(&hi2c1, DISPLAY_I2C_ADDR, 0x04, I2C_MEMADD_SIZE_8BIT, (uint8_t*)com_reg_contents, sizeof(com_reg_contents), HAL_MAX_DELAY);
}

/*! \fn     display_text(char* text, BOOL display_dot)
*   \brief  Display text
*   \param	text		Text to display
*   \param	display_dot	Display the dot
*/
void display_text(char* text, BOOL display_dot)
{
	uint8_t disp_chars[4] = {0,0,0,0};
	uint8_t com_reg_contents[4][3];

	/* memclear */
	memset(com_reg_contents, 0x00, sizeof(com_reg_contents));

	/* Convert test to abcdef... */
	for (uint16_t i = 0; i < 4; i++)
	{
		/* End of string? */
		if (text[i] == 0)
		{
			break;
		}
		else
		{
			disp_chars[i] = SevenSegmentASCII[text[i] - ' '];
		}
	}

	/* Convert to abcdef to com register contents: code for readibility and hope for compiler optimization */
	/* First digit */
	com_reg_contents[0][0] = (((disp_chars[0] >> 0) & 0x01) << 4);
	com_reg_contents[1][0] = (((disp_chars[0] >> 5) & 0x01) << 4);
	com_reg_contents[2][0] = (((disp_chars[0] >> 4) & 0x01) << 4);
	com_reg_contents[0][1] |= (((disp_chars[0] >> 1) & 0x01) << 3);
	com_reg_contents[1][1] |= (((disp_chars[0] >> 6) & 0x01) << 3);
	com_reg_contents[2][1] |= (((disp_chars[0] >> 2) & 0x01) << 3);
	com_reg_contents[3][1] |= (((disp_chars[0] >> 3) & 0x01) << 3);

	/* Second digit */
	com_reg_contents[0][1] |= (((disp_chars[1] >> 1) & 0x01) << 5) | (((disp_chars[1] >> 0) & 0x01) << 4);
	com_reg_contents[1][1] |= (((disp_chars[1] >> 6) & 0x01) << 5) | (((disp_chars[1] >> 5) & 0x01) << 4);
	com_reg_contents[2][1] |= (((disp_chars[1] >> 2) & 0x01) << 5) | (((disp_chars[1] >> 4) & 0x01) << 4);
	com_reg_contents[3][1] |= (((disp_chars[1] >> 3) & 0x01) << 5);

	/* Third digit */
	com_reg_contents[0][1] |= (((disp_chars[2] >> 1) & 0x01) << 7) | (((disp_chars[2] >> 0) & 0x01) << 6);
	com_reg_contents[1][1] |= (((disp_chars[2] >> 6) & 0x01) << 7) | (((disp_chars[2] >> 5) & 0x01) << 6);
	com_reg_contents[2][1] |= (((disp_chars[2] >> 2) & 0x01) << 7) | (((disp_chars[2] >> 4) & 0x01) << 6);
	com_reg_contents[3][1] |= (((disp_chars[2] >> 3) & 0x01) << 7);

	/* Last digit */
	com_reg_contents[0][2] = disp_chars[3] & 0x03;
	com_reg_contents[1][2] = (((disp_chars[3] >> 6) & 0x01) << 1) | (((disp_chars[3] >> 5) & 0x01) << 0);
	com_reg_contents[2][2] = (((disp_chars[3] >> 2) & 0x01) << 1) | (((disp_chars[3] >> 4) & 0x01) << 0);
	com_reg_contents[3][2] = (((disp_chars[3] >> 3) & 0x01) << 1);

	/* Dot? */
	if (display_dot != FALSE)
	{
		com_reg_contents[3][2] |= 0x01;
	}

	/* Update whole display */
	HAL_I2C_Mem_Write(&hi2c1, DISPLAY_I2C_ADDR, 0x04, I2C_MEMADD_SIZE_8BIT, (uint8_t*)com_reg_contents, sizeof(com_reg_contents), HAL_MAX_DELAY);
}

/*! \fn     display_speed(uint16_t speed)
*   \brief  Display speed
*   \param	speed	Speed in tenth of kmh
*/
void display_speed(uint16_t speed)
{
	char temp_buf[10];

	if (speed / 1000 > 0)
	{
		snprintf(temp_buf, sizeof(temp_buf), "%d", speed);
		display_text(temp_buf, TRUE);
	}
	else if (speed / 100 > 0)
	{
		snprintf(temp_buf, sizeof(temp_buf), " %d", speed);
		display_text(temp_buf, TRUE);
	}
	else if (speed / 10 > 0)
	{
		snprintf(temp_buf, sizeof(temp_buf), "  %d", speed);
		display_text(temp_buf, TRUE);
	}
	else
	{
		snprintf(temp_buf, sizeof(temp_buf), "  0%d", speed);
		display_text(temp_buf, TRUE);
	}
}
