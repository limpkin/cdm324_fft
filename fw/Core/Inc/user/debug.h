#ifndef DEBUG_H_
#define DEBUG_H_

#include "stm32f3xx_hal.h"

/* Prototypes */
void debug_dma_output_buffer(uint8_t* buffer, uint16_t size);
void debug_printf(const char *fmt, ...);
void debug_print_string(char* string);
char debug_get_char_from_uart(void);
void debug_init(void);

#endif
