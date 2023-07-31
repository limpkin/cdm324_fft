#ifndef ANALOG_H_
#define ANALOG_H_

#include "stm32f3xx_hal.h"

/* Defines */
#define DOPPLER_Pin GPIO_PIN_0
#define DOPPLER_GPIO_Port GPIOB

/* Prototypes */
uint16_t analog_compute_fft_on_cplted_sequence(BOOL remove_low_freqs);
void analog_output_current_fft_to_uart(uint16_t nb_bins);
BOOL analog_get_and_clear_adc_measurement_done(void);
void analog_output_conversion_buffer_to_uart(void);
void analog_trigger_conversion(void);
void analog_init(void);

#endif
