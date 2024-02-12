from backend.search.signals.signal_utils import connect_signals, disconnect_signals
from backend.tests.utils import not_raises


class TestSignalUtils:
    def test_disconnect_signals_no_errors(self):
        with not_raises(Exception):
            disconnect_signals()

    def test_connect_signals_no_errors(self):
        with not_raises(Exception):
            connect_signals()
