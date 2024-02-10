from backend.search.signals.signal_utils import connect_signals, disconnect_signals


class TestSignalUtils:
    def test_disconnect_signals_no_errors(self):
        disconnect_signals()
        assert True  # just checking that it runs successfully

    def test_connect_signals_no_errors(self):
        connect_signals()
        assert True  # just checking that it runs successfully
