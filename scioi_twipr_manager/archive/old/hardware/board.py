import archive.cm4_core_old2.hardware.interfaces as interfaces


class Board:
    UART_STM32: interfaces.UART
    SPI_STM32: interfaces.SPI
    I2C_EXT: interfaces.I2C

    def __init__(self):
        pass
