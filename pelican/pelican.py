# Pelican - Board Interraction
# Author: Oleksandr Ivanchuk
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import yaml

try:
    from ampy.files import Files
except Exception as e:
    raise Exception(f'Cannot import ampy {e}')


BUFFER_SIZE = 32  # Amount of data to read or write to the serial port at a time.
# This is kept small because small chips and USB to serial
# bridges usually have very small buffers.


class Pelican():
    '''
    Class to use micropython board as CAN interface.
    '''
    def __init__(self, pyboard) -> None:
        '''
        Initialize the micropython board.
        '''
        self._pyboard = pyboard
        self.CAN_MODULE = 'mcpcan.py'


    def _read_config(self, config: str) -> None:
        '''
        Read config file to get parameters of CAN initialization.
        '''
        path = os.path.dirname(__file__)
        with open(os.path.join(path, config), 'r') as conf:
            return yaml.load(conf, Loader=yaml.FullLoader)


    def _check_onboard_file(self) -> None:
        '''
        Check wether the file exist on the board.
        '''
        board = Files(self._pyboard)

        ls = board.ls(long_format=False)

        if ''.join(['/', self.CAN_MODULE]) not in ls:
            print(f'The file `{self.CAN_MODULE}` is being written to the board.')
            path = os.path.dirname(__file__)
            with open(os.path.join(path, self.CAN_MODULE), "rb") as infile:
                data = infile.read()
            board.put(self.CAN_MODULE, data)


    def dump(self, config_file: str) -> None:
        '''
        Gets the message from CAN buffer.

        Example:
        pelican -p /dev/ttyUSB0 -b 115200 dump
        '''
        self._check_onboard_file()

        conf = self._read_config(config_file)

        code = '''\
from mcpcan import CAN
can = CAN(cs={0})
can.start(speed_cfg={1}, crystal={2}, filter={3}, listen_only={4})
res = can.recv_msg()
print(res)\
'''.format(conf['cs'],
           conf['speed'],
           conf['crystal'],
           conf['filter'],
           conf['l'])

        self._pyboard.enter_raw_repl()

        for line in code.split('\n'):
            result = self._pyboard.exec(line)
        self._pyboard.exit_raw_repl()

        return result.decode()


    def send(self, message, config_file) -> None:
        '''
        Sends the CAN message.

        Example:
        pelican -p /dev/ttyUSB0 -b 115200 send -i 123 -d Hello111 -l8 -r False
        '''
        self._check_onboard_file()

        conf = self._read_config(config_file)

        # Make the data to appear as byte array
        message['data'] = message['data'].encode('utf-8')

        code = '''\
from mcpcan import CAN
can = CAN(cs={0})
can.start(speed_cfg={1}, crystal={2}, filter={3}, listen_only={4})
can.send_msg({5})\
'''.format(conf['cs'],
           conf['speed'],
           conf['crystal'],
           conf['filter'],
           conf['l'],
           message)

        self._pyboard.enter_raw_repl()

        for line in code.split('\n'):
            result = self._pyboard.exec(line)
        self._pyboard.exit_raw_repl()

        return (result.decode())


    def blink(self) -> None:
        '''
        Blinks a built-in LED to approve the board is working well.

        Example:
        pelican -p /dev/ttyUSB0 -b 115200 blink
        '''
        code = '''\
from machine import Pin
import time
led = Pin(2, Pin.OUT)
led.on()
led.off()'''
        self._pyboard.enter_raw_repl()

        for line in code.split('\n'):
            print(line)
            self._pyboard.exec(line)

        self._pyboard.exit_raw_repl()
