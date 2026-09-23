#ifndef __SWM350_PORT_H__
#define __SWM350_PORT_H__


void PORT_Init(PORT_TypeDef * PORTx, uint32_t n, uint32_t func, uint32_t digit_in_en);


#define PORTA_PIN0_GPIO         0
#define PORTA_PIN0_FUNMUX0		1
#define PORTA_PIN0_QSPI0_D1		2
#define PORTA_PIN0_LCD_RD      	3
#define PORTA_PIN0_LCD_DCLK		3

#define PORTA_PIN1_GPIO         0
#define PORTA_PIN1_FUNMUX1		1
#define PORTA_PIN1_SWDCK		2
#define PORTA_PIN1_JTAG_TCK  	2

#define PORTA_PIN2_GPIO         0
#define PORTA_PIN2_FUNMUX0		1
#define PORTA_PIN2_SWDIO		2
#define PORTA_PIN2_JTAG_TMS 	2

#define PORTA_PIN3_GPIO         0
#define PORTA_PIN3_FUNMUX1		1
#define PORTA_PIN3_XTAL_IN    	7

#define PORTA_PIN4_GPIO         0
#define PORTA_PIN4_FUNMUX0		1
#define PORTA_PIN4_XTAL_OUT   	7

#define PORTA_PIN5_GPIO         0
#define PORTA_PIN5_FUNMUX1     	1
#define PORTA_PIN5_ADC0_CH4		7

#define PORTA_PIN6_GPIO         0
#define PORTA_PIN6_FUNMUX0		1
#define PORTA_PIN6_SD_D6     	2

#define PORTA_PIN7_GPIO         0
#define PORTA_PIN7_FUNMUX1   	1

#define PORTA_PIN8_GPIO         0
#define PORTA_PIN8_FUNMUX0		1
#define PORTA_PIN8_LCD_CS		2
#define PORTA_PIN8_LCD_VSYNC	2
#define PORTA_PIN8_SD_CMD		3

#define PORTA_PIN9_GPIO         0
#define PORTA_PIN9_FUNMUX1   	1
#define PORTA_PIN9_LCD_B5       2
#define PORTA_PIN9_UART2_CTS	3

#define PORTA_PIN10_GPIO        0
#define PORTA_PIN10_FUNMUX0		1
#define PORTA_PIN10_LCD_B6      2
#define PORTA_PIN10_UART2_RTS	3

#define PORTA_PIN11_GPIO        0
#define PORTA_PIN11_FUNMUX1   	1
#define PORTA_PIN11_LCD_B7      2

#define PORTA_PIN12_GPIO        0
#define PORTA_PIN12_FUNMUX0		1
#define PORTA_PIN12_LCD_G0      2
#define PORTA_PIN12_ADC0_CH5	7

#define PORTA_PIN13_GPIO        0
#define PORTA_PIN13_FUNMUX1   	1
#define PORTA_PIN13_LCD_G1      2
#define PORTA_PIN13_UART1_CTS	3
#define PORTA_PIN13_ADC0_CH6	7

#define PORTA_PIN14_GPIO        0
#define PORTA_PIN14_FUNMUX0		1
#define PORTA_PIN14_QSPI1_CS	2
#define PORTA_PIN14_LCD_G2     	3
#define PORTA_PIN14_UART1_RTS	4

#define PORTA_PIN15_GPIO        0
#define PORTA_PIN15_FUNMUX1   	1
#define PORTA_PIN15_QSPI1_D0	2
#define PORTA_PIN15_LCD_G3     	3
#define PORTA_PIN15_UART0_CTS	4

#define PORTB_PIN0_GPIO         0
#define PORTB_PIN0_FUNMUX0     	1
#define PORTB_PIN0_QSPI0_D2		2

#define PORTB_PIN1_GPIO         0
#define PORTB_PIN1_FUNMUX1		1
#define PORTB_PIN1_SD_DET		2
#define PORTB_PIN1_UART1_CTS	3

#define PORTB_PIN2_GPIO         0
#define PORTB_PIN2_FUNMUX0		1
#define PORTB_PIN2_DVP_CK		2
#define PORTB_PIN2_ADC0_CH13	7

#define PORTB_PIN3_GPIO         0
#define PORTB_PIN3_FUNMUX1		1
#define PORTB_PIN3_JTAG_TRST	2
#define PORTB_PIN3_LCD_B3		3
#define PORTB_PIN3_DVP_D1		4

#define PORTB_PIN4_GPIO         0
#define PORTB_PIN4_FUNMUX0		1
#define PORTB_PIN4_LCD_B7		2
#define PORTB_PIN4_DVP_D0		3

#define PORTB_PIN5_GPIO         0
#define PORTB_PIN5_FUNMUX1		1
#define PORTB_PIN5_LCD_B3		2
#define PORTB_PIN5_DVP_VS		3

#define PORTB_PIN6_GPIO         0
#define PORTB_PIN6_FUNMUX0		1
#define PORTB_PIN6_LCD_B4		2
#define PORTB_PIN6_DVP_HS		3

#define PORTB_PIN7_GPIO         0
#define PORTB_PIN7_FUNMUX1		1
#define PORTB_PIN7_LCD_RD      	2
#define PORTB_PIN7_LCD_DCLK		2
#define PORTB_PIN7_DVP_D4		3

#define PORTB_PIN8_GPIO         0
#define PORTB_PIN8_FUNMUX0		1
#define PORTB_PIN8_LCD_RD      	2
#define PORTB_PIN8_LCD_DCLK		2
#define PORTB_PIN8_SD_D1		3
#define PORTB_PIN8_UART1_RTS	4

#define PORTB_PIN9_GPIO         0
#define PORTB_PIN9_FUNMUX1		1
#define PORTB_PIN9_LCD_R3		2
#define PORTB_PIN9_ADC0_CH14	7

#define PORTB_PIN10_GPIO        0
#define PORTB_PIN10_FUNMUX0		1
#define PORTB_PIN10_JTAG_TDO	2
#define PORTB_PIN10_LCD_B1		3
#define PORTB_PIN10_DVP_D3		4

#define PORTB_PIN11_GPIO        0
#define PORTB_PIN11_FUNMUX1		1
#define PORTB_PIN11_JTAG_TDI	2
#define PORTB_PIN11_LCD_B2		3
#define PORTB_PIN11_DVP_D2		4

#define PORTB_PIN12_GPIO        0
#define PORTB_PIN12_FUNMUX0		1
#define PORTB_PIN12_LCD_B0		2
#define PORTB_PIN12_SD_D7		3
#define PORTB_PIN12_DVP_D8		4

#define PORTB_PIN13_GPIO        0
#define PORTB_PIN13_FUNMUX1		1
#define PORTB_PIN13_LCD_CS		2
#define PORTB_PIN13_LCD_VSYNC	2
#define PORTB_PIN13_DVP_D7		3

#define PORTB_PIN14_GPIO        0
#define PORTB_PIN14_FUNMUX0		1
#define PORTB_PIN14_LCD_WR		2
#define PORTB_PIN14_LCD_HSYNC	2
#define PORTB_PIN14_DVP_D6		3

#define PORTB_PIN15_GPIO        0
#define PORTB_PIN15_FUNMUX1		1
#define PORTB_PIN15_LCD_RS      2
#define PORTB_PIN15_LCD_DEN		2
#define PORTB_PIN15_DVP_D5		3

#define PORTC_PIN0_GPIO         0
#define PORTC_PIN0_FUNMUX0		1
#define PORTC_PIN0_QSPI1_D1		2
#define PORTC_PIN0_LCD_G4		3
#define PORTC_PIN0_UART0_RTS	4

#define PORTC_PIN1_GPIO         0
#define PORTC_PIN1_FUNMUX1		1
#define PORTC_PIN1_QSPI1_D2		2
#define PORTC_PIN1_LCD_G5		3
#define PORTC_PIN1_UART2_CTS	4

#define PORTC_PIN2_GPIO         0
#define PORTC_PIN2_FUNMUX0		1
#define PORTC_PIN2_QSPI1_D3		2
#define PORTC_PIN2_LCD_G6		3
#define PORTC_PIN2_UART2_RTS	4

#define PORTC_PIN3_GPIO         0
#define PORTC_PIN3_FUNMUX1		1
#define PORTC_PIN3_QSPI1_CK		2
#define PORTC_PIN3_LCD_G7		3
#define PORTC_PIN3_UART1_CTS	4

#define PORTC_PIN4_GPIO         0
#define PORTC_PIN4_FUNMUX0		1
#define PORTC_PIN4_LCD_R0		2
#define PORTC_PIN4_UART1_RTS	3
#define PORTC_PIN4_ADC0_CH7		7

#define PORTC_PIN5_GPIO         0
#define PORTC_PIN5_FUNMUX1		1
#define PORTC_PIN5_LCD_R1      	2
#define PORTC_PIN5_UART0_CTS	3
#define PORTC_PIN5_ADC0_CH8		7

#define PORTC_PIN6_GPIO         0
#define PORTC_PIN6_FUNMUX0		1
#define PORTC_PIN6_LCD_R2		2
#define PORTC_PIN6_UART0_RTS	3
#define PORTC_PIN6_ADC0_CH9     7

#define PORTC_PIN7_GPIO         0
#define PORTC_PIN7_FUNMUX1		1
#define PORTC_PIN7_LCD_R3		2

#define PORTC_PIN8_GPIO         0
#define PORTC_PIN8_FUNMUX0		1
#define PORTC_PIN8_LCD_R4		2
#define PORTC_PIN8_ADC0_CH10	7

#define PORTC_PIN9_GPIO         0
#define PORTC_PIN9_FUNMUX1		1
#define PORTC_PIN9_LCD_R5		2

#define PORTC_PIN10_GPIO        0
#define PORTC_PIN10_FUNMUX0		1
#define PORTC_PIN10_LCD_R6		2

#define PORTC_PIN11_GPIO        0
#define PORTC_PIN11_FUNMUX1		1
#define PORTC_PIN11_LCD_R7		2

#define PORTC_PIN12_GPIO        0
#define PORTC_PIN12_FUNMUX0		1
#define PORTC_PIN12_LCD_R4		2

#define PORTC_PIN13_GPIO        0
#define PORTC_PIN13_FUNMUX1		1
#define PORTC_PIN13_LCD_R5		2

#define PORTC_PIN14_GPIO        0
#define PORTC_PIN14_FUNMUX0		1
#define PORTC_PIN14_QSPI0_D3	2
#define PORTC_PIN14_LCD_WR		3
#define PORTC_PIN14_LCD_HSYNC	3

#define PORTC_PIN15_GPIO        0
#define PORTC_PIN15_FUNMUX1		1
#define PORTC_PIN15_QSPI0_CS	2
#define PORTC_PIN15_LCD_RS      3
#define PORTC_PIN15_LCD_DEN		3

#define PORTD_PIN0_GPIO         0
#define PORTD_PIN0_FUNMUX0		1
#define PORTD_PIN0_UART2_RTS	2
#define PORTD_PIN0_ADC0_CH1		7

#define PORTD_PIN1_GPIO         0
#define PORTD_PIN1_FUNMUX1		1
#define PORTD_PIN1_UART2_CTS	2
#define PORTD_PIN1_ADC0_CH0		7

#define PORTD_PIN2_GPIO         0
#define PORTD_PIN2_FUNMUX0		1
#define PORTD_PIN2_UART1_RTS	2
#define PORTD_PIN2_DAC0_OUT		7

#define PORTD_PIN3_GPIO         0
#define PORTD_PIN3_FUNMUX1		1
#define PORTD_PIN3_QSPI0_D0		2
#define PORTD_PIN3_DVP_D13		3

#define PORTD_PIN4_GPIO         0
#define PORTD_PIN4_FUNMUX0     	1
#define PORTD_PIN4_QSPI0_CK		2

#define PORTD_PIN5_GPIO         0
#define PORTD_PIN5_FUNMUX1		1
#define PORTD_PIN5_QSPI0_D3		2
#define PORTD_PIN5_DVP_D12		3

#define PORTD_PIN6_GPIO         0
#define PORTD_PIN6_FUNMUX0		1
#define PORTD_PIN6_QSPI0_D2		2
#define PORTD_PIN6_DVP_D11		3

#define PORTD_PIN7_GPIO         0
#define PORTD_PIN7_FUNMUX1		1
#define PORTD_PIN7_QSPI0_D1		2
#define PORTD_PIN7_DVP_D10		3

#define PORTD_PIN8_GPIO         0
#define PORTD_PIN8_FUNMUX0		1
#define PORTD_PIN8_QSPI0_CS		2
#define PORTD_PIN8_DVP_D9		3

#define PORTD_PIN9_GPIO         0
#define PORTD_PIN9_FUNMUX1		1
#define PORTD_PIN9_UART1_CTS	2
#define PORTD_PIN9_ADC0_CH3		7

#define PORTD_PIN10_GPIO        0
#define PORTD_PIN10_FUNMUX0		1
#define PORTD_PIN10_ADC0_CH2	7

#define PORTD_PIN11_GPIO        0
#define PORTD_PIN11_FUNMUX1		1
#define PORTD_PIN11_UART0_CTS	2

#define PORTD_PIN12_GPIO        0
#define PORTD_PIN12_FUNMUX0		1
#define PORTD_PIN12_LCD_B1		2

#define PORTD_PIN13_GPIO        0
#define PORTD_PIN13_FUNMUX1		1
#define PORTD_PIN13_LCD_B2		2

#define PORTD_PIN14_GPIO        0
#define PORTD_PIN14_FUNMUX0		1
#define PORTD_PIN14_QSPI0_D0	2
#define PORTD_PIN14_LCD_B4		3

#define PORTD_PIN15_GPIO        0
#define PORTD_PIN15_FUNMUX1		1
#define PORTD_PIN15_QSPI0_CK	2
#define PORTD_PIN15_LCD_CS		3
#define PORTD_PIN15_LCD_VSYNC	3

#define PORTE_PIN0_GPIO			0
#define PORTE_PIN0_FUNMUX0		1
#define PORTE_PIN0_UART0_RTS	2
#define PORTE_PIN0_ADC0_CH11	7

#define PORTE_PIN1_GPIO			0
#define PORTE_PIN1_FUNMUX1		1
#define PORTE_PIN1_ADC0_CH12	7

#define PORTE_PIN2_GPIO			0
#define PORTE_PIN2_FUNMUX0		1
#define PORTE_PIN2_SD_D2		2

#define PORTE_PIN3_GPIO			0
#define PORTE_PIN3_FUNMUX1		1
#define PORTE_PIN3_SD_D3		2

#define PORTE_PIN4_GPIO			0
#define PORTE_PIN4_FUNMUX0		1

#define PORTE_PIN5_GPIO			0
#define PORTE_PIN5_FUNMUX1		1
#define PORTE_PIN5_SD_CLK		2
#define PORTE_PIN5_UART2_CTS	3

#define PORTE_PIN6_GPIO			0
#define PORTE_PIN6_FUNMUX0		1
#define PORTE_PIN6_SD_D0		2
#define PORTE_PIN6_UART2_RTS	3

#define PORTE_PIN7_GPIO			0
#define PORTE_PIN7_FUNMUX1		1
#define PORTE_PIN7_LCD_B0		2

#define PORTE_PIN8_GPIO			0
#define PORTE_PIN8_FUNMUX0		1
#define PORTE_PIN8_LCD_B3		2

#define PORTE_PIN9_GPIO			0
#define PORTE_PIN9_FUNMUX1		1
#define PORTE_PIN9_SD_D4		2
#define PORTE_PIN9_UART0_CTS	3

#define PORTE_PIN10_GPIO		0
#define PORTE_PIN10_FUNMUX0		1
#define PORTE_PIN10_SD_D5		2
#define PORTE_PIN10_UART0_RTS	3

#define PORTE_PIN11_GPIO		0
#define PORTE_PIN11_FUNMUX1		1

#define PORTE_PIN12_GPIO		0
#define PORTE_PIN12_FUNMUX0		1
#define PORTE_PIN12_QSPI1_CS	2

#define PORTE_PIN13_GPIO		0
#define PORTE_PIN13_FUNMUX1		1
#define PORTE_PIN13_QSPI1_D1	2

#define PORTE_PIN14_GPIO		0
#define PORTE_PIN14_FUNMUX0		1
#define PORTE_PIN14_QSPI1_CK	2

#define PORTE_PIN15_GPIO		0
#define PORTE_PIN15_FUNMUX1		1
#define PORTE_PIN15_QSPI1_D0	2

#define PORTF_PIN0_GPIO			0
#define PORTF_PIN0_FUNMUX0		1
#define PORTF_PIN0_QSPI1_D2		2

#define PORTF_PIN1_GPIO			0
#define PORTF_PIN1_FUNMUX1		1
#define PORTF_PIN1_QSPI1_D3		2

#define PORTF_PIN2_GPIO			0
#define PORTF_PIN2_FUNMUX0		1

#define PORTF_PIN3_GPIO			0
#define PORTF_PIN3_FUNMUX1		1

#define PORTF_PIN4_GPIO			0
#define PORTF_PIN4_FUNMUX0		1

#define PORTF_PIN5_GPIO			0
#define PORTF_PIN5_FUNMUX1		1

#define PORTF_PIN6_GPIO			0
#define PORTF_PIN6_FUNMUX0		1

#define PORTF_PIN7_GPIO			0
#define PORTF_PIN7_FUNMUX1		1




/* FUNMUX values */
#define FUNMUX0_UART0_TXD	    100
#define FUNMUX0_UART1_TXD	    101
#define FUNMUX0_UART2_TXD	    102
#define FUNMUX0_UART3_TXD	    103
#define FUNMUX0_UART4_TXD		104
#define FUNMUX0_USART0_TXD		105
#define FUNMUX0_PWM0A_OUT	    106
#define FUNMUX0_PWM0B_OUT	    107
#define FUNMUX0_PWM1A_OUT	    108
#define FUNMUX0_PWM1B_OUT	    109
#define FUNMUX0_TIMR0_IN		110
#define FUNMUX0_TIMR0_OUT		110
#define FUNMUX0_TIMR2_IN		111
#define FUNMUX0_TIMR2_OUT		111
#define FUNMUX0_BTIMR0_OUT		112
#define FUNMUX0_BTIMR2_OUT		113
#define FUNMUX0_CAN0_TXD	    114
#define FUNMUX0_CAN1_TXD	    115
#define FUNMUX0_I2C0_SCL	    116
#define FUNMUX0_I2C1_SCL	    117
#define FUNMUX0_I2S0_SCLK		118
#define FUNMUX0_I2S1_SCLK		119
#define FUNMUX0_I2S0_DATA		120
#define FUNMUX0_I2S1_DATA		121
#define FUNMUX0_SPI0_SCLK		122
#define FUNMUX0_SPI1_SCLK		123
#define FUNMUX0_SPI0_MOSI	    124
#define FUNMUX0_SPI1_MOSI	    125
#define FUNMUX0_PWM_CLK0		126
#define FUNMUX0_RTC_OUT			127
#define FUNMUX0_HALL0_IN0		128
#define FUNMUX0_HALL0_IN1		129
#define FUNMUX0_PWM_BRK0		130
#define FUNMUX0_DMA_TRIG0		131

#define FUNMUX1_UART0_RXD	    100
#define FUNMUX1_UART1_RXD	    101
#define FUNMUX1_UART2_RXD	    102
#define FUNMUX1_UART3_RXD	    103
#define FUNMUX1_UART4_RXD	    104
#define FUNMUX1_USART0_RXD	    105
#define FUNMUX1_PWM0AN_OUT	    106
#define FUNMUX1_PWM0BN_OUT	    107
#define FUNMUX1_PWM1AN_OUT	    108
#define FUNMUX1_PWM1BN_OUT	    109
#define FUNMUX1_TIMR1_IN		110
#define FUNMUX1_TIMR1_OUT		110
#define FUNMUX1_TIMR3_IN		111
#define FUNMUX1_TIMR3_OUT		111
#define FUNMUX1_BTIMR1_OUT		112
#define FUNMUX1_BTIMR3_OUT		113
#define FUNMUX1_CAN0_RXD	    114
#define FUNMUX1_CAN1_RXD	    115
#define FUNMUX1_I2C0_SDA	    116
#define FUNMUX1_I2C1_SDA	    117
#define FUNMUX1_I2S0_MCLK		118
#define FUNMUX1_I2S1_MCLK		119
#define FUNMUX1_I2S0_WS			120
#define FUNMUX1_I2S1_WS			121
#define FUNMUX1_SPI0_SSEL	    122
#define FUNMUX1_SPI1_SSEL	    123
#define FUNMUX1_SPI0_MISO		124
#define FUNMUX1_SPI1_MISO		125
#define FUNMUX1_PWM_CLK1		126
#define FUNMUX1_DSI_TE			127
#define FUNMUX1_HALL0_IN2		128
#define FUNMUX1_PWM_BRK1		129
#define FUNMUX1_PWM_BRK2		130
#define FUNMUX1_DMA_TRIG1		131


#endif //__SWM350_PORT_H__
