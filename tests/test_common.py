# coding:utf-8
import unittest.mock

from backoff._common import _next_wait


def test_next_wait_trunc_wait_fn():
    wait_mock = unittest.mock.Mock()
    wait_mock.send.side_effect = lambda x: x + 2

    # 9 + 2 > 10
    assert _next_wait(wait_mock, 9, None, 0, 10) == 10
    wait_mock.send.assert_called_once_with(9)


def test_next_wait_trunc_wait_fn_elapsed():
    wait_mock = unittest.mock.Mock()
    wait_mock.send.side_effect = lambda x: x + 2

    # 4 + 2 > 10 - 5
    assert _next_wait(wait_mock, 4, None, 5, 10) == 5
    wait_mock.send.assert_called_once_with(4)


def test_next_wait_elapsed_wait():
    wait_mock = unittest.mock.Mock()
    wait_mock.send.side_effect = lambda x: x + 2

    assert _next_wait(wait_mock, 0, None, 10, 10) == 0
    wait_mock.send.assert_not_called()
    assert _next_wait(wait_mock, 0, None, 11, 10) == 0
    wait_mock.send.assert_not_called()


def test_next_wait_jitter_over():
    wait_mock = unittest.mock.Mock()
    wait_mock.send.side_effect = lambda x: x + 2

    jitter_fn_mock = unittest.mock.Mock()
    jitter_fn_mock.side_effect = lambda x: x + 2

    # 8 + 2 + 1 > 10
    assert _next_wait(wait_mock, 7, jitter_fn_mock, 0, 10) == 10
    wait_mock.send.assert_called_once_with(7)
    jitter_fn_mock.assert_called_once_with(9)


def test_next_wait_jitter_skipped():
    wait_mock = unittest.mock.Mock()
    wait_mock.send.side_effect = lambda x: x + 2

    jitter_fn_mock = unittest.mock.Mock()
    jitter_fn_mock.side_effect = lambda x: x - 1

    # 8 + 2 == 10
    assert _next_wait(wait_mock, 8, jitter_fn_mock, 0, 10) == 10
    wait_mock.send.assert_called_once_with(8)
    jitter_fn_mock.assert_not_called()


def test_next_wait_jitter_under():
    wait_mock = unittest.mock.Mock()
    wait_mock.send.side_effect = lambda x: x + 2

    jitter_fn_mock = unittest.mock.Mock()
    jitter_fn_mock.side_effect = lambda x: x - 1

    # 7 + 2 - 1 == 8
    assert _next_wait(wait_mock, 7, jitter_fn_mock, 0, 10) == 8
    wait_mock.send.assert_called_once_with(7)
    jitter_fn_mock.assert_called_once_with(9)
