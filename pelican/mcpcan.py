import time
from machine import Pin, SPI


class CAN:
    '''
    Implements the standard CAN communication protocol.
    '''

    def __init__(self, cs: int = 27, interrupt: int = None) -> None:
        '''
        MCP2515 chip initialization

        SPI used by default is HSPI
        id=1, baudrate=10000000, sck=14, mosi=13, miso=12

        CS default is pin 27
        '''
        # Setting up SPI
        self.spi = SPI(1, 10000000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
        self.spi.init()

        self.cs = Pin(cs, Pin.OUT, value=1)
        self.interrupt_pin = interrupt
        self._rx_buf = []

        # Software reset
        self._spi_reset()

        # If you can read the data, it is considered that the initialization
        # is OK. At least the chip is soldered.
        time.sleep(0.2)
        mode = self._spi_read_reg(b'\x0e')
        if (mode == 0):
            raise OSError("MCP2515 init failed (Cannot read any data).")


    def subscribe(self, action: callable) -> None:
        '''
        The method takes a callable object as an input and performs an action
        when externall interrupt triggers.
        '''
        if self.interrupt_pin:
            self.int = Pin(self.interrupt_pin, Pin.IN)
            self.int.irq(trigger=Pin.IRQ_FALLING, handler=action)
        else:
            raise Exception('Interrupt pin ({}) is either not set or not \
correct'.format(self.interrupt_pin))


    def stop(self) -> None:
        '''
        Stops MCP2515
        '''
        self._spi_write_bit(b'\x0f', b'\xe0', b'\x20')  # sleep mode


    def start(self,
              speed_cfg: int = 500,
              crystal: int = 8,
              filter=None,
              listen_only: bool = False) -> None:
        '''
        Starts MCP2515

        speed_cfg: CAN communication speed in Kb/s
        The supported communication speeds are as follows:
            - for 16MHz Crystal Oscillator
        5, 10, 20, 33, 40, 50, 80, 95, 100, 125, 200, 250, 500, 1000
            - for 8MHz Crystal Oscillator
        5, 10, 20, 40, 50, 80, 100, 125, 200, 250, 500

        crystal: defines the frequency of the Crystal Oscillator
                 could be either 8 or 16 MHz

        filter: filter mode for received packets
        TODO

        listen_only: whether to specify the listening mode
        '''
        # Set to configuration mode
        self._spi_reset()
        self._spi_write_bit(b'\x0f', b'\xe0', b'\x80')

        # Set communication rate
        self._set_speed(speed_cfg, crystal)

        # Channel 1 packet filtering settings
        if (filter == None):
            self._spi_write_bit(b'\x60', b'\x64', b'\x64')
        else:
            self._spi_write_bit(b'\x60', b'\x64', b'\x04')
            self._spi_write_reg(b'\x00', filter.get('F0'))
            self._spi_write_reg(b'\x04', filter.get('F1'))
            self._spi_write_reg(b'\x20', filter.get('M0'))

        # Disable channel 2 message reception
        self._spi_write_bit(b'\x70', b'\x60', b'\x00')
        self._spi_write_reg(b'\x08', b'\xff\xff\xff\xff')
        self._spi_write_reg(b'\x10', b'\xff\xff\xff\xff')
        self._spi_write_reg(b'\x14', b'\xff\xff\xff\xff')
        self._spi_write_reg(b'\x18', b'\xff\xff\xff\xff')
        self._spi_write_reg(b'\x24', b'\xff\xff\xff\xff')

        # Set to normal mode or listening mode
        mode = b'\x60' if listen_only else b'\x00'
        self._spi_write_bit(b'\x0f', b'\xe0', mode)


    def _set_speed(self,
                   speed_cfg: int,
                   crystal: int) -> None:
        '''
        Sets communication rate according to used oscillator.
        '''
        speed_cfg_at_16M = {
            1000: b'\x82\xD0\x00',
            500: b'\x86\xF0\x00',
            250: b'\x85\xF1\x41',
            200: b'\x87\xFA\x01',
            125: b'\x86\xF0\x03',
            100: b'\x87\xFA\x03',
            95: b'\x07\xAD\x03',
            80: b'\x87\xFF\x03',
            50: b'\x87\xFA\x07',
            40: b'\x87\xFF\x07',
            33: b'\x07\xBE\x09',
            20: b'\x87\xFF\x0F',
            10: b'\x87\xFF\x1F',
            5: b'\x87\xFF\x3F'
        }

        speed_cfg_at_8M = {
            500: b'\x01\x91\x00',
            250: b'\x03\xac\x00',
            200: b'\x04\xb6\x00',
            125: b'\x03\xac\x01',
            100: b'\x04\xb6\x01',
            80: b'\x02\x92\x04',
            50: b'\x04\xb6\x03',
            40: b'\x04\xb6\x04',
            20: b'\x04\xb6\x09',
            10: b'\x04\xb6\x13',
            5: b'\x04\xb6\x27'
        }

        speed = {
            8: speed_cfg_at_8M,
            16: speed_cfg_at_16M
        }
        if crystal in speed.keys():
            if speed_cfg in speed[crystal].keys():
                cfg = speed[crystal].get(speed_cfg, (b'\x00\x00\x00'))
                print(cfg)
                self._spi_write_reg(b'\x28', cfg)
            else:
                raise Exception('Unsupported speed ({}Kb/s) or oscillator \
settings incorrect.'.format(speed_cfg))
        else:
            raise Exception('Unsupported Crystal Oscillator frequency. \
select from {}'.format(''.join(speed.keys())))

        del speed


    def send_msg(self, msg: dict, send_chanel: int = None) -> None:
        '''
        Send a message.

        msg:
        msg ['id']: ID of the message to be sent
        msg ['ext']: Whether the message to be sent is an extended frame
        msg ['data']: Data of the message to be sent
        msg ['dlc']: Length of the message to be sent
        msg ['rtr']: Whether the message to be sent is a remote frame

        send_chanel:
        Specify the channel for sending packets. The valid values ​​are
        as follows:
        0: channel 0
        1: Channel 1
        2: Channel 2
        MCP2515 provides three sending channels. By default, channel 0 is used.
        TODO: automatically find free channels.
        NOTE: If there are pending messages in the channel, the previous
        message transmission will be stopped.
        Then replace it with a new message and enter the pending state again.
        '''
        if send_chanel == None:
            send_chanel = 0
        # stop message transmission in previous register
        ctl = (((send_chanel % 3) + 3) << 4) .to_bytes(1, 'big')
        self._spi_write_bit(ctl, b'\x08', b'\x00')
        # Data structure
        self.tx_buf = bytearray(13)
        if msg.get('ext'):
            self.tx_buf[0] = ((msg.get('id')) >> 21) & 0xFF
            id_buf = ((msg.get('id')) >> 13) & 0xE0
            id_buf |= 0x08
            id_buf |= ((msg.get('id')) >> 16) & 0x03
            self.tx_buf[1] = id_buf
            self.tx_buf[2] = ((msg.get('id')) >> 8) & 0xFF
            self.tx_buf[3] = (msg.get('id')) & 0xFF
            if msg.get('rtr'):
                self.tx_buf[4] |= 0x40
        else:
            self.tx_buf[0] = ((msg.get('id')) >> 3) & 0xFF
            self.tx_buf[1] = ((msg.get('id')) << 5) & 0xE0
            if msg.get('rtr'):
                self.tx_buf[1] |= 0x10
        if msg.get('rtr') == False:
            self.tx_buf[4] |= msg.get('dlc') & 0x0F
            self.tx_buf[5:13] = msg.get('data')[: msg.get('dlc')]
        # Data loading
        dat = ((((send_chanel % 3) + 3) << 4) + 1) .to_bytes(1, 'big')
        self._spi_write_reg(dat, self.tx_buf)
        # Send
        # self._spi_write_bit (ctl, b'\x08', b'\x08')
        self._spi_send_msg(1 << send_chanel)


    def recv_msg(self) -> dict:
        '''
        Requests whether the MCP2515 has received a message. If so, read it
        in buffer. check_rx is called.
        Requests whether the buffer has packets. If yes, return the earliest
        received frame, otherwise return None.

        Return Msg description:
        msg ['tm']: Time to receive the message [ms]. Timer starts on power on.
        msg ['id']: ID of the received message
        msg ['ext']: Whether the received message is an extended frame
        msg ['data']: Received message data
        msg ['dlc']: Length of received message
        msg ['rtr']: Whether the received message is a remote frame
        NOTE: Only one frame is returned at a time.
        '''
        self.check_rx()
        if len(self._rx_buf) == 0:
            return None
        dat = self._rx_buf.pop(0)
        msg = {}
        msg['tm'] = int.from_bytes(dat[-8:], 'big')
        msg['dlc'] = int.from_bytes(dat[4: 5], 'big') & 0x0F
        msg['data'] = dat[5:13]
        # 0: standard frame 1: extended frame
        ide = (int.from_bytes(dat[1: 2], 'big') >> 3) & 0x01
        msg['ext'] = True if ide == 1 else False
        id_s0_s10 = int.from_bytes(dat[: 2], 'big') >> 5
        id_e16_e17 = int.from_bytes(dat[: 2], 'big') & 0x03
        id_e0_e15 = int.from_bytes(dat[2: 4], 'big')
        if msg['ext']:
            msg['id'] = (id_s0_s10 << 18) + (id_e16_e17 << 16) + id_e0_e15
            msg['rtr'] = True if (int.from_bytes(
                dat[4: 5], 'big') & 0x40) else False
        else:
            msg['id'] = id_s0_s10
            msg['rtr'] = True if (int.from_bytes(
                dat[1: 2], 'big') & 0x10) else False
        return msg


    def get_smpl(self, printable=True):
        '''
        Query whether the MCP2515 has received a message. If so, deposit it in Buf. check_rx is called.
        Query whether Buf has packets. If yes, return the earliest received frame, otherwise return None.
        Return Msg description:
        '''
        self.check_rx()
        if len(self._rx_buf) == 0:
            return None
        dat = self._rx_buf.pop(0)
        msg = {}

        msg['dlc'] = int.from_bytes(dat[4: 5], 'big') & 0x0F
        msg['data'] = dat[5:13]
        msg['id'] = int.from_bytes(dat[: 2], 'big') >> 5

        if print:
            return '{}  [{}]  {}'.format(hex(msg['id']), msg['dlc'], msg['data'].decode())
        else:
            return msg


    def check_rx(self):
        '''
        Query whether the MCP2515 has received a message. If so, store it in Buf and return TRUE, otherwise return False.
        Note: Failure to store the messages in the MCP into Buf in time may result in the MCP being unable to receive new messages.
        In other words, packets may be lost.
        So, try to call this function as much as possible ~~
        '''
        rx_flag = int.from_bytes(self._spi_ReadStatus(), 'big')
        if (rx_flag & 0x01):
            dat = self._spi_RecvMsg(0)
            tm = (time.ticks_ms()). to_bytes(8, 'big')
            self._rx_buf.append(dat + tm)
        if (rx_flag & 0x02):
            dat = self._spi_RecvMsg(1)
            tm = (time.ticks_ms()). to_bytes(8, 'big')
            self._rx_buf.append(dat + tm)
        return True if (rx_flag & 0b11000000) else False


    def _spi_reset(self):
        '''
        MCP2515_SPI instruction-reset
        '''
        self.cs.off()
        self.spi.write(b'\xc0')
        self.cs.on()


    def _spi_write_reg(self, addr, value):
        '''
        MCP2515_SPI instruction-write register
        '''
        self.cs.off()
        self.spi.write(b'\x02')
        self.spi.write(addr)
        self.spi.write(value)
        self.cs.on()


    def _spi_read_reg(self, addr, num=1):
        '''
        MCP2515_SPI instruction-read register
        '''
        self.cs.off()
        self.spi.write(b'\x03')
        self.spi.write(addr)
        buf = self.spi.read(num)
        self.cs.on()
        return buf


    def _spi_write_bit(self, addr, mask, value):
        '''
        MCP2515_SPI instruction-bit modification
        '''
        self.cs.off()
        self.spi.write(b'\x05')
        self.spi.write(addr)
        self.spi.write(mask)
        self.spi.write(value)
        self.cs.on()


    def _spi_ReadStatus(self):
        '''
        MCP2515_SPI instruction-read status
        '''
        self.cs.off()
        self.spi.write(b'\xa0')
        buf = self.spi.read(1)
        self.cs.on()
        return buf


    def _spi_RecvMsg(self, select):
        '''
        MCP2515_SPI instruction-read Rx buffer
        '''
        self.cs.off()
        if select == 0:
            self.spi.write(b'\x90')
            buf = self.spi.read(13)
        if select == 1:
            self.spi.write(b'\x94')
            buf = self.spi.read(13)
        self.cs.on()
        return buf


    def _spi_send_msg(self, select):
        '''
        MCP2515_SPI instruction-Request to send a message
        '''
        self.cs.off()
        self.spi.write((0x80 + (select & 0x07)). to_bytes(1, 'big'))
        self.cs.on()
