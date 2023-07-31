#include "user/defines.h"
#include "user/debug.h"
#include <string.h>
#include <stdarg.h>
#include <stdio.h>
/* Boolean set when a DMA TX transfer is in progress */
volatile BOOL debug_uart_tx_in_progress = FALSE;
/* DMA transfer for UART TX */
DMA_HandleTypeDef hdma_usart2_tx;
/* Board UART */
UART_HandleTypeDef debug_huart2;


/*! \fn     USART2_IRQHandler(void)
*   \brief  USART2 IRQ
*/
void USART2_IRQHandler(void)
{
	HAL_UART_IRQHandler(&debug_huart2);
}

/*! \fn     DMA1_Channel7_IRQHandler(void)
*   \brief  Called by interrupt after completed DMA transfer
*/
void DMA1_Channel7_IRQHandler(void)
{
	HAL_DMA_IRQHandler(debug_huart2.hdmatx);
}

/*! \fn     HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
*   \brief  Function called by interrupt at the end of the DMA transfer
*   \param	huart	Pointer to the UART handle that brought up this interrupt
*/
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
	debug_uart_tx_in_progress = FALSE;
}

/*! \fn     debug_init(void)
*   \brief  Debug initialization code
*/
void debug_init(void)
{
	GPIO_InitTypeDef GPIO_InitStruct = {0};

	/* DMA controller clock enable */
	__HAL_RCC_DMA1_CLK_ENABLE();

	/* USART clock enable */
    __HAL_RCC_USART2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

	/* Configure GPIO pins */
	GPIO_InitStruct.Pin = GPIO_PIN_2|GPIO_PIN_3;
	GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
	GPIO_InitStruct.Alternate = GPIO_AF7_USART2;
	HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

	/* DMA1_Channel7_IRQn interrupt configuration */
	HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
	HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);

	/* USART2 DMA Init */
	hdma_usart2_tx.Instance = DMA1_Channel7;
	hdma_usart2_tx.Init.Direction = DMA_MEMORY_TO_PERIPH;
	hdma_usart2_tx.Init.PeriphInc = DMA_PINC_DISABLE;
	hdma_usart2_tx.Init.MemInc = DMA_MINC_ENABLE;
	hdma_usart2_tx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
	hdma_usart2_tx.Init.MemDataAlignment = DMA_MDATAALIGN_BYTE;
	hdma_usart2_tx.Init.Mode = DMA_NORMAL;
	hdma_usart2_tx.Init.Priority = DMA_PRIORITY_HIGH;
	HAL_DMA_Init(&hdma_usart2_tx);

	/* Link DMA handler with uart struct */
	__HAL_LINKDMA(&debug_huart2,hdmatx,hdma_usart2_tx);

	/* UART init */
	debug_huart2.Instance = USART2;
	debug_huart2.Init.BaudRate = 1000000;
	debug_huart2.Init.WordLength = UART_WORDLENGTH_8B;
	debug_huart2.Init.StopBits = UART_STOPBITS_1;
	debug_huart2.Init.Parity = UART_PARITY_NONE;
	debug_huart2.Init.Mode = UART_MODE_TX_RX;
	debug_huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
	debug_huart2.Init.OverSampling = UART_OVERSAMPLING_16;
	debug_huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
	debug_huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
	HAL_UART_Init(&debug_huart2);

	/* Peripheral interrupt init*/
	HAL_NVIC_SetPriority(USART2_IRQn, 0, 0);
	HAL_NVIC_EnableIRQ(USART2_IRQn);
}

/*! \fn     debug_print_string(char* string)
*   \brief  Send debug print over UART
*   \param	string	0-terminated string to be sent over
*/
void debug_print_string(char* string)
{
	while(debug_uart_tx_in_progress != FALSE);
	debug_uart_tx_in_progress = TRUE;
    HAL_UART_Transmit_DMA(&debug_huart2, (uint8_t*)string, strlen(string));
	while(debug_uart_tx_in_progress != FALSE);
}

/*! \fn     debug_printf(const char *fmt, ...)
*   \brief  UART printf
*/
void debug_printf(const char *fmt, ...)
{
    char buf[64];
    va_list ap;

    va_start(ap, fmt);

    if (vsnprintf(buf, sizeof(buf), fmt, ap) > 0)
    {
        va_end(ap);
    }
    else
    {
        va_end(ap);
    }

    debug_print_string(buf);
}

/*! \fn     debug_dma_output_buffer(uint8_t* buffer, uint16_t size)
*   \brief  Send buffer over UART
*   \param	buffer	pointer to the buffer
*   \param	size	buffer size
*   \note	Please note that this is done using DMA and isn't blocking!
*/
void debug_dma_output_buffer(uint8_t* buffer, uint16_t size)
{
	while(debug_uart_tx_in_progress != FALSE);
	debug_uart_tx_in_progress = TRUE;
    HAL_UART_Transmit_DMA(&debug_huart2, buffer, size);
}

/*! \fn     debug_get_char_from_uart(void)
*   \brief  Get debug char from UART
*   \return	0 if nothing was received, otherwise the char
*/
char debug_get_char_from_uart(void)
{
	char temp_char = 0;

	if ((__HAL_UART_GET_FLAG(&debug_huart2, UART_FLAG_RXNE) ? SET : RESET) == SET)
	{
		HAL_UART_Receive(&debug_huart2, (uint8_t*)&temp_char, sizeof(temp_char), 1);
		return temp_char;
	}
	else
	{
		return 0;
	}
}
