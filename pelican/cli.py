import click
import yaml
import os

from pelican import pelican
from pelican import pyboard

_board = None
config_file = 'config.yaml'

@click.group()
@click.option(
    "-p","--port",
    required=False,
    type=click.STRING,
    help="The name of the board's serial port",
)
@click.option(
    "-b", "--baud",
    default=115200,
    type=click.INT,
    help="The baudrate for the communication.",
)
def cli(**kwargs):
    """peliCAN is a simple tool for CAN communication via micropython board.

    The tool is being utilized for sending and receiving CAN frames.
    """
    global _board
    _board = pyboard.Pyboard(kwargs['port'], baudrate=kwargs['baud'])


@cli.command()
@click.option(
    '--cs',
    default=27,
    type=click.INT,
    help='''CS signal of MCP2515 module.'''
)
@click.option(
    '-s', '--speed',
    default=500,
    type=click.INT,
    help='''Data tramsmission speed.'''
)
@click.option(
    '-c', '--crystal',
    default=8,
    type=click.INT,
    help='''The frequency of the crystal oscillator placed on MCP2515 board.'''
)
@click.option(
    '-f', '--filter',
    default=None,
    help='''Not implemented yet.'''
)
@click.option(
    'l', '--listen-only',
    is_flag=True,
    required=False,
    default=False,
    help='''Init CAN bus in listen only mode.'''
)
def setup_config(**kwargs):
    '''
    Setup CAN configuration.

    Example:
    pelican setup-config --cs 23 -s 500 -c 8
    '''
    path = os.path.dirname(__file__)
    with open(os.path.join(path, config_file), 'w') as conf:
        conf.write(yaml.dump(kwargs))

    print(f'config successfull\n{kwargs}')


@cli.command()
def dump(**kwargs):
    '''
    Gets the frame from CAN buffer.
    '''
    print(f'dump\n{kwargs}')


@cli.command()
@click.option(
    '-i', '--id',
    required=True,
    type=click.INT,
    help='''The id of the CAN frame.'''
)
@click.option(
    '-x', '--ext',
    required=True,
    default=False,
    type=click.BOOL,
    help = '''Whether the message to be sent is an extended frame.'''
)
@click.option(
    '-d', '--data',
    required=True,
    type=click.STRING,
    help = '''Data of the message to be sent.'''
)
@click.option(
    '-l', '--dlc',
    required=True,
    type=click.INT,
    help = '''Length of the message to be sent.'''
)
@click.option(
    '-r', '--rtr',
    required=False,
    default=False,
    type=click.BOOL,
    help = '''Whether the message to be sent is a remote frame.'''
)
def send(**kwargs):
    '''
    Send's the frame with entered data.

    Example:
    {'ext':False, 'id':0x18ff50e5, 'data':b'\x12\x34\x56\x78\x90\xab\xcd\xef', 'dlc':8, 'rtr':False}
    '''
    print(f'send\n{kwargs}')


@cli.command()
def blink(**kwargs):
    '''
    Blinks the built-in LED.
    '''
    board = pelican.Pelican(_board)
    board.blink()


def main():
    try:
        cli()
    finally:
        if _board is not None:
            try:
                _board.close()
            except:
                pass

if __name__ == "__main__":
    main()