#ifndef __SWM221_PORT_H__
#define __SWM221_PORT_H__

void PORT_Init(PORT_TypeDef * PORTx, uint32_t n, uint32_t func, uint32_t digit_in_en);	//端口引脚功能选择，其可取值如下：


#define PORTA_PIN0_GPIO         0
#define PORTA_PIN0_MPU_D7		1
#define PORTA_PIN0_I2C0_SCL     2
#define PORTA_PIN0_UART0_RX     3
#define PORTA_PIN0_PWM0AN       4
#define PORTA_PIN0_PWM1BN       5
#define PORTA_PIN0_PWM0A        6

#define PORTA_PIN1_GPIO         0
#define PORTA_PIN1_I2C0_SDA     1
#define PORTA_PIN1_UART0_TX     2
#define PORTA_PIN1_PWM1BN       3
#define PORTA_PIN1_PWM1B        4

#define PORTA_PIN2_GPIO         0
#define PORTA_PIN2_USART0_TX	1
#define PORTA_PIN2_PWM1AN       2
#define PORTA_PIN2_PWM0AN       3
#define PORTA_PIN2_PWM1A        4

#define PORTA_PIN3_GPIO         0
#define PORTA_PIN3_USART0_RX	1
#define PORTA_PIN3_PWM0A        2
#define PORTA_PIN3_PWM1AN       3
#define PORTA_PIN3_PWM0AN       4

#define PORTA_PIN4_GPIO         0
#define PORTA_PIN4_UART1_TX     1
#define PORTA_PIN4_PWM1B        2
#define PORTA_PIN4_PWM1AN		3
#define PORTA_PIN4_PWM1BN       4

#define PORTA_PIN5_GPIO         0
#define PORTA_PIN5_UART1_RX     1
#define PORTA_PIN5_PWM1A        2
#define PORTA_PIN5_PWM0AN       3
#define PORTA_PIN5_PWM1AN       4

#define PORTA_PIN6_GPIO         0
#define PORTA_PIN6_I2C0_SCL     1
#define PORTA_PIN6_USART0_TX	2
#define PORTA_PIN6_CAN0_RX		3
#define PORTA_PIN6_PWM0B        4
#define PORTA_PIN6_BTIMR0_OUT	5

#define PORTA_PIN7_GPIO         0
#define PORTA_PIN7_I2C0_SDA     1
#define PORTA_PIN7_USART0_RX	2
#define PORTA_PIN7_CAN0_TX		3
#define PORTA_PIN7_PWM0BN       4
#define PORTA_PIN7_BTIMR1_OUT	5

#define PORTA_PIN8_GPIO         0
#define PORTA_PIN8_MPU_D0		1
#define PORTA_PIN8_SPI0_SCLK    2
#define PORTA_PIN8_QSPI0_SCLK	3
#define PORTA_PIN8_ADC0_CH2     7
#define PORTA_PIN8_OPA1_OUT     7

#define PORTA_PIN9_GPIO         0
#define PORTA_PIN9_MPU_D1		1
#define PORTA_PIN9_USART0_TX	2
#define PORTA_PIN9_SPI0_MOSI	3
#define PORTA_PIN9_QSPI0_MOSI	4
#define PORTA_PIN9_OPA1_INP     7

#define PORTA_PIN10_GPIO        0
#define PORTA_PIN10_MPU_D2		1
#define PORTA_PIN10_USART0_RX	2
#define PORTA_PIN10_SPI0_MISO	3
#define PORTA_PIN10_QSPI0_MISO	4
#define PORTA_PIN10_OPA1_INN    7

#define PORTA_PIN11_GPIO        0
#define PORTA_PIN11_MPU_D3		1
#define PORTA_PIN11_SPI0_SSEL	2
#define PORTA_PIN11_QSPI0_SSEL	3
#define PORTA_PIN11_PWM_CLK1    4
#define PORTA_PIN11_ADC0_CH1    7
#define PORTA_PIN11_ADC_REFP	7

#define PORTA_PIN12_GPIO        0
#define PORTA_PIN12_MPU_D4		1
#define PORTA_PIN12_UART1_TX	2
#define PORTA_PIN12_QSPI0_D2	3
#define PORTA_PIN12_ADC1_CH1	7
#define PORTA_PIN12_ACMP1_INN   7

#define PORTA_PIN13_GPIO        0
#define PORTA_PIN13_MPU_D5		1
#define PORTA_PIN13_UART1_RX	2
#define PORTA_PIN13_QSPI0_D3	3
#define PORTA_PIN13_ADC1_CH0    7

#define PORTA_PIN14_GPIO        0
#define PORTA_PIN14_MPU_D6		1
#define PORTA_PIN14_TIMR0_IN    2
#define PORTA_PIN14_TIMR0_OUT   3
#define PORTA_PIN14_ADC0_CH0    7
#define PORTA_PIN14_ACMP1_INP   7

#define PORTA_PIN15_GPIO        0
#define PORTA_PIN15_QSPI0_MOSI	1
#define PORTA_PIN15_PWM1A		2
#define PORTA_PIN15_HALL_IN2	3

#define PORTB_PIN0_GPIO         0
#define PORTB_PIN0_UART1_TX    	1
#define PORTB_PIN0_QSPI0_MISO	2
#define PORTB_PIN0_BTIMR2_OUT	3
#define PORTB_PIN0_TIMR0_IN		4
#define PORTB_PIN0_TIMR0_OUT	5
#define PORTB_PIN0_ADC1_CH6		7
#define PORTB_PIN0_OPA2_INN    	7

#define PORTB_PIN1_GPIO         0
#define PORTB_PIN1_UART1_RX    	1
#define PORTB_PIN1_QSPI0_D2		2
#define PORTB_PIN1_BTIMR3_OUT	3
#define PORTB_PIN1_TIMR2_IN		4
#define PORTB_PIN1_TIMR2_OUT	5
#define PORTB_PIN1_OPA2_INP    	7

#define PORTB_PIN2_GPIO         0
#define PORTB_PIN2_UART0_TX     1
#define PORTB_PIN2_QSPI0_D3		2
#define PORTB_PIN2_BTIMR0_OUT	3
#define PORTB_PIN2_TIMR1_IN		4
#define PORTB_PIN2_TIMR1_OUT	5
#define PORTB_PIN2_ADC0_CH8		7
#define PORTB_PIN2_OPA2_OUT    	7

#define PORTB_PIN3_GPIO         0
#define PORTB_PIN3_UART0_RX     1
#define PORTB_PIN3_BTIMR1_OUT	2
#define PORTB_PIN3_TIMR2_IN		3
#define PORTB_PIN3_TIMR2_OUT	4
#define PORTB_PIN3_ACMP0_INN	7

#define PORTB_PIN4_GPIO         0
#define PORTB_PIN4_MPU_CS		1
#define PORTB_PIN4_QEI_A		2
#define PORTB_PIN4_I2C0_SCL     3
#define PORTB_PIN4_QSPI0_MOSI	4
#define PORTB_PIN4_HALL_IN0     5
#define PORTB_PIN4_ADC0_CH7     7
#define PORTB_PIN4_ACMP0_INP2   7

#define PORTB_PIN5_GPIO         0
#define PORTB_PIN5_MPU_RS		1
#define PORTB_PIN5_QEI_B		2
#define PORTB_PIN5_I2C0_SDA     3
#define PORTB_PIN5_HALL_IN1     4
#define PORTB_PIN5_TIMR1_IN     5
#define PORTB_PIN5_TIMR1_OUT    6
#define PORTB_PIN5_ADC0_CH6     7
#define PORTB_PIN5_ACMP0_INP1   7

#define PORTB_PIN6_GPIO         0
#define PORTB_PIN6_MPU_WR		1
#define PORTB_PIN6_QEI_Z		2
#define PORTB_PIN6_PWM_BRK1     3
#define PORTB_PIN6_HALL_IN2     4
#define PORTB_PIN6_TIMR0_IN     5
#define PORTB_PIN6_TIMR0_OUT    6
#define PORTB_PIN6_ADC0_CH5     7
#define PORTB_PIN6_ACMP0_INP0   7

#define PORTB_PIN7_GPIO         0
#define PORTB_PIN7_QEI_DIR		1
#define PORTB_PIN7_UART1_TX     2
#define PORTB_PIN7_CAN0_RX		3
#define PORTB_PIN7_TIMR2_IN     4
#define PORTB_PIN7_TIMR2_OUT    5
#define PORTB_PIN7_ADC1_CH3     7
#define PORTB_PIN7_OPA0_INP     7

#define PORTB_PIN8_GPIO         0
#define PORTB_PIN8_UART1_RX     1
#define PORTB_PIN8_CAN0_TX		2
#define PORTB_PIN8_OPA0_INN     7

#define PORTB_PIN9_GPIO         0
#define PORTB_PIN9_MPU_RD		1
#define PORTB_PIN9_ADC1_CH2     7
#define PORTB_PIN9_OPA0_OUT     7

#define PORTB_PIN10_GPIO        0
#define PORTB_PIN10_UART1_TX	1
#define PORTB_PIN10_UART1_RX	2
#define PORTB_PIN10_SPI0_SCLK	3
#define PORTB_PIN10_PWM0AN      4
#define PORTB_PIN10_TIMR0_IN    5
#define PORTB_PIN10_TIMR0_OUT   6

#define PORTB_PIN11_GPIO        0
#define PORTB_PIN11_UART0_TX    1
#define PORTB_PIN11_SPI0_SCLK	2
#define PORTB_PIN11_PWM0BN      3
#define PORTB_PIN11_TIMR1_IN    4
#define PORTB_PIN11_TIMR1_OUT   5
#define PORTB_PIN11_XTAL_OUT	7

#define PORTB_PIN12_GPIO        0
#define PORTB_PIN12_UART0_RX    1
#define PORTB_PIN12_SPI0_MOSI	2
#define PORTB_PIN12_PWM0B       3
#define PORTB_PIN12_TIMR2_IN    4
#define PORTB_PIN12_TIMR2_OUT   5
#define PORTB_PIN12_XTAL_IN		7

#define PORTB_PIN13_GPIO        0
#define PORTB_PIN13_SPI0_MOSI	1
#define PORTB_PIN13_PWM0A       2

#define PORTB_PIN14_GPIO        0
#define PORTB_PIN14_USART0_TX	1
#define PORTB_PIN14_UART0_TX    2
#define PORTB_PIN14_SPI0_MISO	3
#define PORTB_PIN14_PWM_BRK0    4
#define PORTB_PIN14_BTIMR2_OUT	5
#define PORTB_PIN14_ADC1_CH9   	7

#define PORTB_PIN15_GPIO        0
#define PORTB_PIN15_USART0_RX	1
#define PORTB_PIN15_UART0_RX    2
#define PORTB_PIN15_SPI0_SSEL	3
#define PORTB_PIN15_BTIMR3_OUT	4
#define PORTB_PIN15_TIMR0_IN	5
#define PORTB_PIN15_TIMR0_OUT	6
#define PORTB_PIN15_ADC1_CH8	7

#define PORTC_PIN0_GPIO         0
#define PORTC_PIN0_SWCLK        1
#define PORTC_PIN0_UART1_TX     2
#define PORTC_PIN0_PWM_CLK0     3
#define PORTC_PIN0_TIMR1_IN		4
#define PORTC_PIN0_TIMR1_OUT	5
#define PORTC_PIN0_ADC1_CH7		7

#define PORTC_PIN1_GPIO         0
#define PORTC_PIN1_SWDIO        1
#define PORTC_PIN1_UART1_RX     2
#define PORTC_PIN1_BTIMR3_OUT   3

#define PORTC_PIN2_GPIO         0
#define PORTC_PIN2_I2C0_SCL     1
#define PORTC_PIN2_UART0_TX     2
#define PORTC_PIN2_QSPI0_SSEL	3
#define PORTC_PIN2_CAN0_RX		4
#define PORTC_PIN2_PWM0A		5
#define PORTC_PIN2_HALL_IN0		6

#define PORTC_PIN3_GPIO         0
#define PORTC_PIN3_I2C0_SDA     1
#define PORTC_PIN3_UART0_RX     2
#define PORTC_PIN3_QSPI0_SCLK	3
#define PORTC_PIN3_CAN0_TX		4
#define PORTC_PIN3_PWM0B        5
#define PORTC_PIN3_HALL_IN1		7

#endif //__SWM221_PORT_H__
