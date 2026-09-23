#ifndef __SWM231_PORT_H__
#define __SWM231_PORT_H__

void PORT_Init(PORT_TypeDef * PORTx, uint32_t n, uint32_t func, uint32_t digit_in_en);	//端口引脚功能选择，其可取值如下：


#define PORTA_PIN0_GPIO         0
#define PORTA_PIN0_TIMR0_IN		1
#define PORTA_PIN0_TIMR0_OUT	2
#define PORTA_PIN0_OPA1_INN		7
#define PORTA_PIN0_ACMP1_INN	7

#define PORTA_PIN1_GPIO         0
#define PORTA_PIN1_TIMR0_IN     1
#define PORTA_PIN1_TIMR0_OUT	2
#define PORTA_PIN1_ADC0_CH0		7
#define PORTA_PIN1_ADC0_REFP	7
#define PORTA_PIN1_ACMP1_INP	7

#define PORTA_PIN2_GPIO         0
#define PORTA_PIN2_UART0_TX		1
#define PORTA_PIN2_PWM0AN       2
#define PORTA_PIN2_PWM1BN       3
#define PORTA_PIN2_PWM0A        4

#define PORTA_PIN3_GPIO         0
#define PORTA_PIN3_UART0_RX		1
#define PORTA_PIN3_PWM1BN       2
#define PORTA_PIN3_PWM1B       	3

#define PORTA_PIN4_GPIO         0
#define PORTA_PIN4_SPI0_SCLK    1
#define PORTA_PIN4_PWM1AN       2
#define PORTA_PIN4_PWM0AN		3
#define PORTA_PIN4_PWM1A       	4

#define PORTA_PIN5_GPIO         0
#define PORTA_PIN5_SPI0_MOSI    1
#define PORTA_PIN5_PWM0A        2
#define PORTA_PIN5_PWM1AN       3
#define PORTA_PIN5_PWM0AN       4

#define PORTA_PIN6_GPIO         0
#define PORTA_PIN6_UART1_TX     1
#define PORTA_PIN6_SPI0_MISO	2
#define PORTA_PIN6_PWM1B		3
#define PORTA_PIN6_PWM1AN       4
#define PORTA_PIN6_PWM1BN		5

#define PORTA_PIN7_GPIO         0
#define PORTA_PIN7_UART1_RX     1
#define PORTA_PIN7_SPI0_SSEL	2
#define PORTA_PIN7_PWM1A		3
#define PORTA_PIN7_PWM0AN       4
#define PORTA_PIN7_PWM1AN		5

#define PORTA_PIN8_GPIO         0
#define PORTA_PIN8_UART0_TX		1
#define PORTA_PIN8_PWM_CLK0		2
#define PORTA_PIN8_HALL_IN1		3
#define PORTA_PIN8_ADC0_CH10    7
#define PORTA_PIN8_XTAL_OUT		7

#define PORTA_PIN9_GPIO         0
#define PORTA_PIN9_UART0_RX		1
#define PORTA_PIN9_PWM_BRK0		2
#define PORTA_PIN9_PWM_CLK1		3
#define PORTA_PIN9_HALL_IN2		4
#define PORTA_PIN9_TIMR0_IN     5
#define PORTA_PIN9_TIMR0_OUT	6
#define PORTA_PIN9_XTAL_IN		7

#define PORTA_PIN10_GPIO        0
#define PORTA_PIN10_RESET		7

#define PORTB_PIN0_GPIO         0
#define PORTB_PIN0_SWCLK    	1
#define PORTB_PIN0_UART1_TX		2
#define PORTB_PIN0_HALL_IN0		3
#define PORTB_PIN0_BTIMR0_OUT	4
#define PORTB_PIN0_TIMR0_IN		5
#define PORTB_PIN0_TIMR0_OUT	6
#define PORTB_PIN0_ADC0_CH11   	7

#define PORTB_PIN1_GPIO         0
#define PORTB_PIN1_SWDIO    	1
#define PORTB_PIN1_UART1_RX		2
#define PORTB_PIN1_BTIMR1_OUT	3

#define PORTB_PIN2_GPIO         0
#define PORTB_PIN2_PWM_BRK1     1
#define PORTB_PIN2_BTIMR2_OUT	2

#define PORTB_PIN3_GPIO         0
#define PORTB_PIN3_SPI0_SCLK    1
#define PORTB_PIN3_HALL_IN0		2
#define PORTB_PIN3_ADC0_CH9		7
#define PORTB_PIN3_ACMP0_INP2	7

#define PORTB_PIN4_GPIO         0
#define PORTB_PIN4_UART0_TX		1
#define PORTB_PIN4_SPI0_MOSI	2
#define PORTB_PIN4_HALL_IN1     3
#define PORTB_PIN4_ADC0_CH8		7
#define PORTB_PIN4_ACMP0_INP1	7

#define PORTB_PIN5_GPIO         0
#define PORTB_PIN5_UART0_RX		1
#define PORTB_PIN5_SPI0_MISO	2
#define PORTB_PIN5_HALL_IN2     3
#define PORTB_PIN5_ADC0_CH7		7
#define PORTB_PIN5_OPA0_OUT		7
#define PORTB_PIN5_ACMP0_INP0	7

#define PORTB_PIN6_GPIO         0
#define PORTB_PIN6_SPI0_SSEL	1
#define PORTB_PIN6_PWM0B		2
#define PORTB_PIN6_BTIMR0_OUT   3
#define PORTB_PIN6_TIMR0_IN     4
#define PORTB_PIN6_TIMR0_OUT   	5
#define PORTB_PIN6_ADC0_CH6     7
#define PORTB_PIN6_OPA0_INP		7

#define PORTB_PIN7_GPIO         0
#define PORTB_PIN7_UART1_TX		1
#define PORTB_PIN7_PWM0BN		2
#define PORTB_PIN7_ADC0_CH5		7
#define PORTB_PIN7_OPA0_INN		7
#define PORTB_PIN7_ACMP0_INN	7

#define PORTB_PIN8_GPIO         0
#define PORTB_PIN8_UART1_RX     1
#define PORTB_PIN8_BTIMR1_OUT	2
#define PORTB_PIN8_ADC0_CH4		7
#define PORTB_PIN8_OPA1_OUT     7

#define PORTB_PIN9_GPIO         0
#define PORTB_PIN9_BTIMR2_OUT	1
#define PORTB_PIN9_ADC0_CH1     7
#define PORTB_PIN9_OPA1_INP     7

#define PORTB_PIN10_GPIO        0
#define PORTB_PIN10_ADC0_CH13	7


#endif //__SWM231_PORT_H__
