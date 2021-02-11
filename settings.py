from inspect import isclass
from lora.setting import Setting
import lora.registers as regs            

class LongRangeMode(Setting):
    reg = regs.OP_MODE
    shift = 7
    mask = 0b10000000
    options = ['FSK/OOK', 'LoRa']

class AccessSharedReg(Setting):
    reg = regs.OP_MODE
    shift = 6
    mask = 0b01000000

class LowFrequencyModeOn(Setting):
    reg = regs.OP_MODE
    shift = 3
    mask = 0b00001000
    
class Mode(Setting):
    reg = regs.OP_MODE
    mask = 0b00000111
    options = [
        'SLEEP', 'STDBY', 'FSTX', 'TX',
        'FSRX', 'RXCONTINOUS', 'RXSINGLE', 'CAD'
    ]

class CarrierFrequency(Setting):
    reg = regs.FR_MSB
    num_bytes = 3

    @classmethod
    def forward_transform(cls, v):
        return int(v * 2**19 / int(32e6))

    @classmethod
    def reverse_transform(cls, v):
        return int(v * int(32e6) / 2**19)
    
class PaSelect(Setting):
    reg = regs.PA_CONFIG
    shift = 7
    mask = 0b10000000
    options = ['RFO', 'PA_BOOST']

class MaxPower(Setting):
    reg = regs.PA_CONFIG
    shift = 4
    mask = 0b01110000

class OutputPower(Setting):
    reg = regs.PA_CONFIG
    mask = 0b00001111

class PaRamp(Setting):
    reg = regs.PA_RAMP
    mask = 0b00001111
    options = [
        '34ms', '2ms', '1ms', '500us', '250us', '125us', '100us', '62us',
        '50us', '40us', '31us', '25us', '20us', '15us', '12us', '10us'
    ]

class OcpOn(Setting):
    reg = regs.OCP
    shift = 5
    mask = 0b00100000

class OcpTrim(Setting):
    reg = regs.OCP
    mask = 0b00011111
    options = [
        '45', '50', '55', '60', '65', '70', '75', '80',
        '85', '90', '95', '100', '105', '110', '115',
        '120', '130', '140', '150', '160', '170', '180',
        '190', '200', '210', '220', '230', '240'
    ]

class LnaGain(Setting):
    reg = regs.LNA
    shift = 5
    mask = 0b11100000
    options = [
        None, 'G1', 'G2', 'G3',
        'G4', 'G5', 'G6', None
    ]

class LnaBoostLf(Setting):
    reg = regs.LNA
    shift = 3
    mask = 0b00001100
    
class LnaBoostHf(Setting):
    reg = regs.LNA
    mask = 0b00000011

class FifoAddrPtr(Setting):
    reg = regs.FIFO_ADDR_PTR
    
class FifoTxBaseAddr(Setting):
    reg = regs.FIFO_TX_BASE_ADDR

class FifoRxBaseAddr(Setting):
    reg = regs.FIFO_RX_BASE_ADDR

class Bandwidth(Setting):
    reg = regs.MODEM_CONFIG_1
    shift = 4
    mask = 0b11110000
    options = [
        '7.8kHz', '10.4kHz', '15.6kHz', '20.8kHz', '31.25kHz',
        '41.7kHz', '62.5kHz', '125kHz', '250kHz', '500kHz'
    ]    
    
class CodingRate(Setting):
    reg = regs.MODEM_CONFIG_1
    shift = 1
    mask = 0b00001110
    options = [
        None, '4/5', '4/6', '4/7', '4/8'
    ]
        
class ImplicitHeaderModeOn(Setting):
    reg = regs.MODEM_CONFIG_1
    mask = 0b00000001
    
class SpreadingFactor(Setting):
    reg = regs.MODEM_CONFIG_2
    shift = 4
    mask = 0b11110000

class TxContinousMode(Setting):
    reg = regs.MODEM_CONFIG_2
    shift = 3
    mask = 0b00001000
    
class RxPayloadCrcOn(Setting):
    reg = regs.MODEM_CONFIG_2
    shift = 2
    mask = 0b00000100


class PaDac(Setting):
    reg = regs.PA_DAC
    mask = 0b00000111
    options = [
        None, None, None, None,
        'default', None, None, '+20dBm'
    ]

class SyncWord(Setting):
    reg = regs.SYNC_WORD

class LowDataRateOptimize(Setting):
    reg = regs.MODEM_CONFIG_3
    shift = 3
    mask = 0b00001000
    
class PreambleLength(Setting):
    reg = regs.PREAMBLE_MSB
    num_bytes = 2

class AgcAutoOn(Setting):
    reg = regs.MODEM_CONFIG_3
    shift = 2
    mask = 0b00000100
    
class DetectionOptimize(Setting):
    reg = regs.DETECT_OPTIMIZE
    mask = 0b00000111

class DetectionThreshold(Setting):
    reg = regs.DETECTION_THRESHOLD
    

options = {
    cls.id(): cls
    for cls in globals().values()
    if isclass(cls) and issubclass(cls, Setting) and cls is not Setting
}

if __name__ == '__main__':
    for k, v in options.items():
        print(k, v.__name__)
