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


BUFFER_SIZE = 32  # Amount of data to read or write to the serial port at a time.
# This is kept small because small chips and USB to serial
# bridges usually have very small buffers.


class Pelican():
    '''

    '''
    def __init__(self, pyboard) -> None:
        '''
        Initialize the MicroPython board files class using the provided pyboard
        instance. In most cases you should create a Pyboard instance (from
        pyboard.py) which connects to a board over a serial connection and pass
        it in.
        '''
        self._pyboard = pyboard


    def blink(self) -> None:
        '''
        Blinks a built-in LED to approve the board is working well.
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
