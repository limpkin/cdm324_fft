#ifndef DISPLAY_H_
#define DISPLAY_H_

#include "stm32f3xx_hal.h"
#include "defines.h"

/* Defines */
#define DISPLAY_I2C_ADDR	0x70

/* Prototypes */
void display_text(char* text, BOOL display_dot);
void display_animation_step(uint16_t anim_step);
void display_speed(uint16_t speed);
BOOL display_init(void);

#endif
