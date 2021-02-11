import pigpio
import atexit

pi = pigpio.pi()

class SPI:
    def __init__(self, channel, baud=32000, flags=0):
        self._h = pi.spi_open(channel, baud, flags)
        atexit.register(self.cleanup)
        
    def read(self, request_n):
        receive_n, data = pi.spi_read(self._h, request_n)
        # TODO: handle when request_n != receive_n
        return data
        
    def write(self, data):
        pi.spi_write(self._h, data)

    def xfer(self, data):
        n, r_data = pi.spi_xfer(self._h, data)
        return r_data

    def cleanup(self):
        pi.spi_close(self._h)
