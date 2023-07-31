#include "user/defines.h"
#include "user/analog.h"
#include "user/debug.h"
#include "arm_math.h"
DMA_HandleTypeDef hdma_adc1;
ADC_HandleTypeDef analog_hadc1;
volatile uint16_t analog_result_buffer1[1024];
volatile uint16_t analog_result_buffer2[1024];
volatile uint16_t* analog_cur_adc_dest_buf_pt;
volatile uint16_t* analog_cplt_adc_dest_buf_pt;
volatile BOOL analog_fdma_transfer_started;
volatile BOOL analog_adc_train_done_flag;
arm_rfft_fast_instance_f32 analog_fft;
float32_t analog_temp_float_array[1024];
float32_t analog_rfft_output[1024];
uint16_t analog_last_peak_indexes[32];
uint16_t analog_cur_peak_fill_idx = 0;


/*! \fn     DMA1_Channel1_IRQHandler(void)
*   \brief  Called by interrupt after completed DMA transfer
*/
void DMA1_Channel1_IRQHandler(void)
{
	HAL_DMA_IRQHandler(analog_hadc1.DMA_Handle);
}

/*! \fn     HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
*   \brief  Function called by interrupt at the end of the DMA transfer
*   \param	hadc	Pointer to the adc handle that brought up this interrupt
*/
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
	analog_trigger_conversion();
	analog_adc_train_done_flag = TRUE;
}

/*! \fn     analog_init(void)
*   \brief  Analog inputs initialization code
*   \notes	The ADC is configured at 64M/128/(1.5+12.5)=35.7kHz sampling rate (3us sampling time)
*/
void analog_init(void)
{
	GPIO_InitTypeDef GPIO_InitStruct = {0};
	ADC_ChannelConfTypeDef sConfig = {0};

	/* DMA controller clock enable */
	__HAL_RCC_DMA1_CLK_ENABLE();

	/* ADC1 & GPIOB clock enable */
    __HAL_RCC_ADC1_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

	/* DMA1_Channel1_IRQn interrupt configuration */
	HAL_NVIC_SetPriority(DMA1_Channel1_IRQn, 0, 0);
	HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn);

	/* Configure GPIO pin : DOPPLER_Pin */
	GPIO_InitStruct.Pin = DOPPLER_Pin;
	GPIO_InitStruct.Mode = GPIO_MODE_ANALOG;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	HAL_GPIO_Init(DOPPLER_GPIO_Port, &GPIO_InitStruct);

    /* ADC1 DMA Init */
    hdma_adc1.Instance = DMA1_Channel1;
    hdma_adc1.Init.Direction = DMA_PERIPH_TO_MEMORY;
    hdma_adc1.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_adc1.Init.MemInc = DMA_MINC_ENABLE;
    hdma_adc1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
    hdma_adc1.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
    hdma_adc1.Init.Mode = DMA_NORMAL;
    hdma_adc1.Init.Priority = DMA_PRIORITY_HIGH;
    HAL_DMA_Init(&hdma_adc1);

    /* Link DMA hander with ADC struct */
    __HAL_LINKDMA(&analog_hadc1,DMA_Handle,hdma_adc1);

	/* Configure ADC */
	analog_hadc1.Instance = ADC1;
	analog_hadc1.Init.ClockPrescaler = ADC_CLOCK_ASYNC_DIV1;
	analog_hadc1.Init.Resolution = ADC_RESOLUTION_12B;
	analog_hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
	analog_hadc1.Init.ContinuousConvMode = ENABLE;
	analog_hadc1.Init.DiscontinuousConvMode = DISABLE;
	analog_hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
	analog_hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
	analog_hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
	analog_hadc1.Init.NbrOfConversion = 1;
	analog_hadc1.Init.DMAContinuousRequests = DISABLE;
	analog_hadc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
	analog_hadc1.Init.LowPowerAutoWait = DISABLE;
	analog_hadc1.Init.Overrun = ADC_OVR_DATA_OVERWRITTEN;
	HAL_ADC_Init(&analog_hadc1);

	/* Configure Regular Channel */
	sConfig.Channel = ADC_CHANNEL_11;
	sConfig.Rank = ADC_REGULAR_RANK_1;
	sConfig.SingleDiff = ADC_SINGLE_ENDED;
	sConfig.SamplingTime = ADC_SAMPLETIME_1CYCLE_5;
	sConfig.OffsetNumber = ADC_OFFSET_NONE;
	sConfig.Offset = 0;
	HAL_ADC_ConfigChannel(&analog_hadc1, &sConfig);

	/* Dual buffer pointing */
	analog_cur_adc_dest_buf_pt = analog_result_buffer1;
	analog_cplt_adc_dest_buf_pt = analog_result_buffer2;
	analog_fdma_transfer_started = FALSE;
	analog_adc_train_done_flag = FALSE;

	/* FFT library initialization */
	arm_rfft_fast_init_f32(&analog_fft, ARRAY_SIZE(analog_result_buffer1));
}

/*! \fn     analog_trigger_conversion(void)
*   \brief  Trigger ADC conversion train
*/
void analog_trigger_conversion(void)
{
	if (analog_cur_adc_dest_buf_pt == analog_result_buffer1)
	{
		analog_cur_adc_dest_buf_pt = analog_result_buffer2;
		analog_cplt_adc_dest_buf_pt = analog_result_buffer1;
	}
	else
	{
		analog_cur_adc_dest_buf_pt = analog_result_buffer1;
		analog_cplt_adc_dest_buf_pt = analog_result_buffer2;
	}

	if (analog_fdma_transfer_started == FALSE)
	{
		HAL_ADC_Start_DMA(&analog_hadc1, (uint32_t*)analog_cur_adc_dest_buf_pt, sizeof(analog_result_buffer1)/sizeof(analog_result_buffer1[0]));
		analog_fdma_transfer_started = TRUE;
	}
	else
	{
        /* Rearm DMA transfer */
		HAL_DMA_Start_IT(analog_hadc1.DMA_Handle, (uint32_t)&analog_hadc1.Instance->DR, (uint32_t)analog_cur_adc_dest_buf_pt, sizeof(analog_result_buffer1)/sizeof(analog_result_buffer1[0]));

        /* Tayoooo */
        SET_BIT(analog_hadc1.Instance->CR, ADC_CR_ADSTART);
	}
}

/*! \fn     analog_get_and_clear_adc_measurement_done(void)
*   \brief  Get and clear ADC measurement done flag
*/
BOOL analog_get_and_clear_adc_measurement_done(void)
{
	volatile BOOL return_bool;

	 __disable_irq();
	 return_bool = analog_adc_train_done_flag;
	 analog_adc_train_done_flag = FALSE;
	 __enable_irq();

	 return (BOOL)return_bool;
}

/*! \fn     analog_output_conversion_buffer_to_uart(void)
*   \brief  Does what it says
*/
void analog_output_conversion_buffer_to_uart(void)
{
	debug_dma_output_buffer((uint8_t*)analog_cplt_adc_dest_buf_pt, sizeof(analog_result_buffer1));
}

/*! \fn     analog_output_current_fft_to_uart(uint16_t nb_bins)
*   \brief  Does what it says
*   \param	nb_bins	Number of bins to send
*/
void analog_output_current_fft_to_uart(uint16_t nb_bins)
{
	debug_dma_output_buffer((uint8_t*)analog_temp_float_array, nb_bins*sizeof(float32_t));
}

/*! \fn     analog_compute_fft_on_cplted_sequence(BOOL remove_low_freqs)
*   \brief  Compute FFT on completed adc samples
*   \param	remove_low_freqs	Set to TRUE to remove low frequencies (~10km/h)
*   \return	FFT peak, to be converted to kmh or mph
*/
uint16_t analog_compute_fft_on_cplted_sequence(BOOL remove_low_freqs)
{
	float32_t max_value;
	uint32_t max_index;

	/* Convert to float */
	for(uint16_t i = 0; i < ARRAY_SIZE(analog_result_buffer1); i++)
	{
		analog_temp_float_array[i] = (float)analog_cplt_adc_dest_buf_pt[i];
	}

	/* RFFT transform */
	arm_rfft_fast_f32(&analog_fft, analog_temp_float_array, analog_rfft_output, 0);

	/* Calculate magnitude of imaginary coefficients */
	arm_cmplx_mag_f32(analog_rfft_output, analog_temp_float_array, ARRAY_SIZE(analog_result_buffer1)/2);

	/* Up to here takes 2.4ms in Release configuration on a 64MHz STM32F301 MCU */

	/* Remove low freqs ? */
	if (remove_low_freqs != FALSE)
	{
		memset(analog_temp_float_array, 0, sizeof(analog_temp_float_array[0])*10);
	}

	/* Set DC component to 0 */
	analog_temp_float_array[0] = 0;

	/* Extract peak frequency */
	arm_max_f32(analog_temp_float_array, ARRAY_SIZE(analog_result_buffer1)/2, &max_value, &max_index);

	/* Fill current peak index if peak is valid */
	if (max_value < 40000)
	{
		analog_last_peak_indexes[analog_cur_peak_fill_idx++] = 0;
	}
	else
	{
		analog_last_peak_indexes[analog_cur_peak_fill_idx++] = max_index;
	}

	/* Handle buffer wrapover */
	if (analog_cur_peak_fill_idx == ARRAY_SIZE(analog_last_peak_indexes))
	{
		analog_cur_peak_fill_idx = 0;
	}

	/* Compute average speed over buffer */
	float32_t cumul = 0;
	uint16_t valid_samples = 0;
	for (uint16_t i = 0; i < ARRAY_SIZE(analog_last_peak_indexes); i++)
	{
		if (analog_last_peak_indexes[i] != 0)
		{
			cumul += (float32_t)analog_last_peak_indexes[i];
			valid_samples++;
		}
	}

	/* Return averaged speed from this */
	float32_t max_freq = 0;
	if (valid_samples != 0)
	{
		max_freq = cumul/valid_samples;
	}
	max_freq = max_freq * 35714 / ARRAY_SIZE(analog_result_buffer1);
	return (uint16_t)max_freq;
}
