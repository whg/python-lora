import time
import atexit
from enum import IntFlag
from spidev import SpiDev
import RPi.GPIO as gpio
from . import registers as regs
from . import settings

class IrqFlags(IntFlag):
    CAD_DETECTED = 1
    FHSS_CHANGE_CHANNEL = 2
    CAD_DONE = 4
    TX_DONE = 8
    VALID_HEADER = 16
    PAYLOAD_CRC_ERROR = 32
    RX_DONE = 64
    RX_TIMEOUT = 128

WRITE_BIT = 0x80

class Lora:
    def __init__(self, reset_pin, spi_channel=0):
        gpio.setmode(gpio.BCM)
        gpio.setup(reset_pin, gpio.OUT)
        self.reset_pin = reset_pin

        self.reset()
        self.spi = SpiDev()
        self.spi.open(0, spi_channel)
        self.spi.max_speed_hz = 1000000

        atexit.register(self.cleanup)

        self.settings_cache = {}
        self.mode = 'SLEEP'
        self.long_range_mode = 'LoRa'
        self.fifo_tx_base_addr = 0
        self.fifo_rx_base_addr = 0
        self.mode = 'STDBY'
        self.clear_irqs()

    def cleanup(self):
        gpio.cleanup()
        self.spi.close()

    def connected(self):
        return self.long_range_mode == 'LoRa'

    def reset(self):
        gpio.output(self.reset_pin, 0)
        time.sleep(0.001)
        gpio.output(self.reset_pin, 1)
        time.sleep(0.005)

    def xfer(self, reg, data=[0]):
        if type(data) is not list:
            data = [data]
        output = self.spi.xfer([reg] + data)
        time.sleep(0.001)
        return output

    def read_reg(self, reg):
        return self.xfer(reg)[1]

    def write_reg(self, reg, value):
        self.xfer(reg | WRITE_BIT, value)

    def read_data(self, reg, n):
        return self.xfer(reg, [0] * n)[1:]

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
        self.fifo_addr_ptr = rx_addr
        n_bytes = self.read_reg(regs.RX_NB_BYTES)
        payload = self.read_data(regs.FIFO, n_bytes)
        rssi = self.adjust_rssi(self.read_reg(regs.PKT_RSSI_VALUE))
        self.clear_irqs(IrqFlags.RX_DONE)
        return list(payload), rssi

    def on_rx(self, pin, func):
        def callback(*args):
            data, rssi = self.read_rx()
            func(data, rssi)

        gpio.setup(pin, gpio.IN)
        gpio.add_event_detect(pin, gpio.RISING, callback=callback)

        # if we're ready now, go for it!
        if gpio.input(pin):
            callback()

    def send(self, data):
        if not data:
            return

        mode_before = self.mode
        self.mode = 'STDBY'

        self.fifo_addr_ptr = 0
        self.write_reg(regs.FIFO, data)
        self.write_reg(regs.PAYLOAD_LENGTH, len(data))
        self.mode = 'TX'

        while True:
            if IrqFlags.TX_DONE in self.irq_flags:
                self.clear_irqs(IrqFlags.TX_DONE)
                break
            time.sleep(0.01)

        self.mode = mode_before

    def __repr__(self):
        lines = []
        for name, cls in settings.options.items():
            lines.append(f'{cls.__name__}: {getattr(self, name)}')
        return '\n'.join(lines)
