#include "user/expander_board.h"
#include "user/display.h"
#include "user/defines.h"
#include "user/analog.h"
#include "user/clocks.h"
#include "user/debug.h"
#include "user/main.h"
// Do we skip data analysis after updating display?
//#define SKIP_ADC_DATA_AFTER_DISPLAY
// After how many FFTs do we update display
#define FFT_CNT_DISP 10
// Define to enable current transient test
//#define CUR_TRANSIENT_TEST


/*! \fn     main_user(void)
*   \brief  User main
*/
void main_user(void)
{
	BOOL output_debug_enabled = FALSE;
	BOOL sd_card_initialized = FALSE;
	BOOL remove_low_freqs = FALSE;
	uint16_t last_fft_return = 0;
	uint16_t fft_nb_counter = 0;
	uint16_t idle_anim_st = 0;
#ifdef CUR_TRANSIENT_TEST
	uint16_t temp_counter = 0;
#endif

	/* Clock init */
	clocks_init();

	/* Debug init */
	debug_init();

	/* Say hello! */
	debug_printf("CDM324 fw v%d.%d, compiled %s %s\r\n", FW_MAJOR, FW_MINOR, __DATE__, __TIME__);

	/* Display init */
	if (display_init() == FALSE)
	{
		debug_print_string("Display not found!\r\n");
		while(1);
	}

	/* Analog input init */
	analog_init();

	/* IO expander init */
	if (expander_init() != FALSE)
	{
		sd_card_initialized = TRUE;
	}

	/* Trigger analog conversions */
	analog_trigger_conversion();

	while (1)
	{
		/* Sequence of ADC measurements complete? */
		if(analog_get_and_clear_adc_measurement_done() != FALSE)
		{
			/* Every few ms we display the speed and depending on define not do anything with the data has the current draw is enough to have an impact on the +5V PSU */
			if (fft_nb_counter++ == FFT_CNT_DISP)
			{
				/* Reset counter */
				fft_nb_counter = 0;
			}
#ifdef SKIP_ADC_DATA_AFTER_DISPLAY
			else
#endif
			{
				/* Should we display the result? */
				if (fft_nb_counter == FFT_CNT_DISP)
				{
#ifndef CUR_TRANSIENT_TEST
					/* Valid return? */
					if (last_fft_return == 0)
					{
						/* Idle animation */
						display_animation_step(idle_anim_st++);
						if (idle_anim_st == 12)
						{
							idle_anim_st = 0;
						}
					}
					else
					{
						/* Convert to mph or kph depending on user selection */
						if (expander_is_kph_selected() != FALSE)
						{
							display_speed((uint16_t)(last_fft_return * 0.2262295));
						}
						else
						{
							display_speed((uint16_t)(last_fft_return * 0.1449275));
						}
					}
#else
					/* Code to test current transient */
					if ((temp_counter++ & 0x0001) == 0)
						display_text("", FALSE);
					else
						display_speed(8888);
#endif
				}

				/* Debug ADC output buffer ? */
				if(output_debug_enabled != FALSE)
				{
					analog_output_conversion_buffer_to_uart();
				}

				/* Compute FFT */
				last_fft_return = analog_compute_fft_on_cplted_sequence(remove_low_freqs);

				/* Debug FFT output buffer ? */
				if(output_debug_enabled != FALSE)
				{
					analog_output_current_fft_to_uart(150);
				}

				/* Commands from UART */
				char uart_input = debug_get_char_from_uart();
				if(uart_input == 'a')
				{
					output_debug_enabled = TRUE;
				}
				else if(uart_input == 's')
				{
					output_debug_enabled = FALSE;
				}
				else if(uart_input == 'h')
				{
					remove_low_freqs = TRUE;
				}
				else if(uart_input == 'l')
				{
					remove_low_freqs = FALSE;
				}
				else if(uart_input == 'k')
				{
					debug_printf("%d\r\n", (uint16_t)(last_fft_return * 0.2262295));
				}
				else if(uart_input == 'm')
				{
					debug_printf("%d\r\n", (uint16_t)(last_fft_return * 0.1449275));
				}
			}
		}

	}
}
