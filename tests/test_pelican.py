import os
from unittest.mock import patch

import pelican
from pelican.pelican import Pelican


_board = patch("ampy.pyboard.Pyboard")
instance = Pelican(_board)


@patch('builtins.open', autospec=True)
@patch('yaml.load')
def test__read_config(yaml, opn):
    '''
    Test of `Pelican._read_config`.
    '''
    instance._read_config('hello')

    opn.assert_called_once()
    yaml.assert_called_once()


@patch('builtins.open', autospec=True)
@patch('builtins.print', autospec=True)
@patch('ampy.files.Files.put', autospec=True)
@patch('ampy.files.Files.ls', autospec=True)
def test__check_onboard_file(ls, put, prnt, opn):
    '''
    Test `Pelican._check_onboard_file`.
    '''
    CAN_MODULE = 'mcpcan.py'
    path = os.path.dirname(pelican.__file__)

    instance._check_onboard_file()

    ls.assert_called_once()
    prnt.assert_called_once_with('The file `mcpcan.py` is being \
written to the board.')
    opn.assert_called_once_with(f'{os.path.join(path, CAN_MODULE)}', 'rb')
    put.assert_called_once()


@patch("ampy.pyboard.Pyboard")
@patch('pelican.pelican.Pelican._check_onboard_file', autospec=True)
@patch('pelican.pelican.Pelican._read_config', autospec=True)
def test_dump(config, check, pyboard):
    '''
    Test `Pelican.dump`.
    '''
    config.return_value = {
        'cs': 1,
        'speed': 1,
        'crystal': 1,
        'filter': 1,
        'l': 1
    }

    instance = Pelican(pyboard)
    instance.dump('file')

    check.assert_called_once()
    config.assert_called_once()
    pyboard.enter_raw_repl.assert_called_once()
    pyboard.exec.assert_called()
    pyboard.exit_raw_repl.assert_called_once()


@patch("ampy.pyboard.Pyboard")
@patch('pelican.pelican.Pelican._check_onboard_file', autospec=True)
@patch('pelican.pelican.Pelican._read_config', autospec=True)
def test_send(config, check, pyboard):
    '''
    Test `Pelican.send`.
    '''
    config.return_value = {
        'cs': 1,
        'speed': 1,
        'crystal': 1,
        'filter': 1,
        'l': 1
    }

    instance = Pelican(pyboard)
    instance.send({'data': 'message'}, 'file')

    check.assert_called_once()
    config.assert_called_once()
    pyboard.enter_raw_repl.assert_called_once()
    pyboard.exec.assert_called()
    pyboard.exit_raw_repl.assert_called_once()


@patch("ampy.pyboard.Pyboard")
def test_blink(pyboard):
    '''
    Test `Pelican.blink`.
    '''
    instance = Pelican(pyboard)
    instance.blink()

    pyboard.enter_raw_repl.assert_called_once()
    pyboard.exec.assert_called()
    pyboard.exit_raw_repl.assert_called_once()
