import time
from enum import IntFlag
from lora.hardware import pi, pigpio, SPI
from lora import registers as regs
from lora import settings

class IrqFlags(IntFlag):
    CAD_DETECTED = 1
    FHSS_CHANGE_CHANNEL = 2
    CAD_DONE = 4
    TX_DONE = 8
    VALID_HEADER = 16
    PAYLOAD_CRC_ERROR = 32
    RX_DONE = 64
    RX_TIMEOUT = 128

class Lora:
    def __init__(self, reset_pin, spi_channel=0):
        self.reset_pin = reset_pin
        pi.set_mode(self.reset_pin, pigpio.OUTPUT)

        self.reset()
        self.spi = SPI(spi_channel)

        self.settings_cache = {}
        self.long_range_mode = 'LoRa'
        self.fifo_tx_base_addr = 0
        self.fifo_rx_base_addr = 0
        self.mode = 'STDBY'
        
    def reset(self):
        for l in range(2):
            pi.write(self.reset_pin, 0)
            time.sleep(0.001)

    def xfer(self, reg, data=[0]):
        if type(data) is not list:
            data = [data]
        return self.spi.xfer([reg] + data)

    def read_reg(self, reg):
        return self.xfer(reg)[1]

    def write_reg(self, reg, value):
        self.xfer(reg | 0x80, value)

    def read_data(self, reg, n):
        return self.xfer(reg, [0] * n)[1:]

    def write_data(self, reg, data):
        self.xfer(reg, data)
        
    def _get_setting(self, setting):
        if setting.num_bytes == 1:
            reg_value = self.read_reg(setting.reg)
            v = (reg_value & setting.mask) >> setting.shift
        else:
            data = self.read_data(setting.reg, setting.num_bytes)
            v = int.from_bytes(data, 'big')
        return setting.decode(v)
        
    def _write_setting(self, setting, value):
        v = setting.encode(value)
        self.settings_cache[setting.id()] = v
        
        if setting.mask != 0xff:
            r = self.read_reg(setting.reg) & (setting.mask ^ 0xff)
            self.write_reg(setting.reg, r | v << setting.shift)
        elif setting.num_bytes == 1:
            self.write_reg(setting.reg, v)
        elif setting.num_bytes > 1:
            vs = list(v.to_bytes(setting.num_bytes, 'big'))
            self.write_reg(setting.reg, vs)
        
    def __getattr__(self, name):
        setting_class = settings.options.get(name)
        if setting_class:
            return self._get_setting(setting_class)
        return self.__dict__[name]
        
    def __setattr__(self, name, value):
        setting_class = settings.options.get(name)
        if setting_class:
            return self._write_setting(setting_class, value)
        
        self.__dict__[name] = value

    @property
    def irq_flags(self):
        return IrqFlags(self.read_reg(regs.IRQ_FLAGS))

    def clear_irqs(self, flags=IrqFlags(0xff)):
        self.write_reg(regs.IRQ_FLAGS, flags)

    def adjust_rssi(self, v):
        # default freq is 434MHz
        freq = self.settings_cache.get('carrier_frequency', 434e6)
        adj = 157 if freq >= 779e6 else 164
        return v - adj

    @property
    def rx_ready(self):
        return IrqFlags.RX_DONE in self.irq_flags
        
    def read_rx(self):
        rx_addr = self.read_reg(regs.FIFO_RX_CURRENT_ADDR)
        self.fifo_add_ptr = rx_addr
        self.ffadfasdf = 3
        n_bytes = self.read_reg(regs.RX_NB_BYTES)
        payload = self.read_data(regs.FIFO, n_bytes)
        rssi = self.adjust_rssi(self.read_reg(regs.PKT_RSSI_VALUE))
        self.clear_irqs(IrqFlags.RX_DONE)
        return list(payload), rssi

    def on_rx(self, pin, func):
        def callback(*args):
            data, rssi = self.read_rx()
            func(data, rssi)
            
        pi.set_mode(pin, pigpio.INPUT)
        pi.callback(pin, pigpio.RISING_EDGE, callback)

        # if we're ready now, go for it!
        if pi.read(pin):
            callback()

    def __repr__(self):
        lines = []
        for name, cls in settings.options.items():
            lines.append(f'{cls.__name__}: {getattr(self, name)}')
        return '\n'.join(lines)


if __name__ == '__main__':
    lora = Lora(reset_pin=22)
    lora.header_mode = 'explicit'
    lora.error_coding_rate = '4/8'
    lora.bandwidth = '125kHz'
    lora.spreading_factor = 7
    lora.enable_crc = False
    lora.sync_word = 0x12
    lora.preamble_length = 6
    lora.detection_optimize = 0x03 # 0x05 for SF6, 0x03 otherwise
    lora.detection_threshold = 0x0a # 0x0c for SF6, 0x0a otherwise
    lora.carrier_frequency = 434e6
    lora.lna_boost_hf = False
    lora.lna_gain = 'G1' # highest gain
    lora.ocp_on = True
    lora.ocp_trim = 200
    lora.mode = 'RXCONTINOUS'

    def c(data, rssi):
        print(data, rssi)

    lora.on_rx(4, c)
    input()
    # print(lora.rx_ready, lora.read_rx())
        
