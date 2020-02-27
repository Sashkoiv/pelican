# peliCAN
A simple wrapper to send and receive CAN frames with micropython board and MCP2515.

![CI](https://github.com/Sashkoiv/pelican/workflows/CI/badge.svg?branch=master)

![Logo](doc/logo.jpg)

## Getting started
1. Connect MCP module to the ESP32.

    MCP2515    | ESP32
    -----      | -----
    VCC        | VIN
    GND        | GND
    CS         | D27
    MISO       | D12
    MOSI       | D13
    SCK        | D14
    INT        | D26

1. Flash the module with micropython as described [here](https://micropython.org/download#esp32)
1. Install [Adafruit ampy](https://github.com/scientifichackers/ampy)
1. Enjoy!

## CLI guide

### Options
Command                 | Description
-----                   | -----
`-p`, `--port` TEXT     | The name of the board's serial port
`-b`, `--baud` INTEGER  | The baudrate for the communication.
`--help`                | Show this message and exit.

### Commands
Command           | Description
-----             | -----
`blink`           | Blinks the built-in LED.
`dump`            | Gets the frame from CAN buffer.
`send`            | Send's the frame with entered data.
`setup-config`    | Setup CAN configuration.

### Usage examples
`setup-config`
```
pelican -p /dev/ttyUSB0 setup-config --cs 27 -s 500 -c 8 -l False
```

`blink`
```
pelican -p /dev/ttyUSB0 blink
```

`dump`
```
pelican -p /dev/ttyUSB0 dump
```

`send`
```
pelican -p /dev/ttyUSB0 -b 115200 send -i 123 -d Hello123 -l8 -r False
```
