from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command


@pytest.mark.django_db
class TestRebuildIndex:
    """
    This class only contains integration tests and does not
    test the manager.rebuild() itself as that should be covered
    in its own unit tests.
    """

    @staticmethod
    def call_command(*args, **kwargs):
        call_command(
            "rebuild_index",
            *args,
            **kwargs,
        )

    def setup_method(self):
        self.mock_connection = MagicMock()
        self.mock_manager = MagicMock()

    def test_base_case(self, caplog):
        # Testing all indices are rebuild if no args are passed.
        with patch(
            "elasticsearch.dsl.connections.Connections.get_connection",
            return_value=self.mock_connection,
        ), patch(
            "backend.management.commands.rebuild_index.Command.index_managers",
            {
                "MOCK_MANAGER": self.mock_manager,
            },
        ):
            self.call_command()

        assert self.mock_manager.rebuild.called

        assert "No index name provided. Building all indices." in caplog.text
        assert "Index rebuild complete." in caplog.text

    def test_valid_index_name_passed(self, caplog):
        # Testing all indices are rebuild if no args are passed.
        with patch(
            "elasticsearch.dsl.connections.Connections.get_connection",
            return_value=self.mock_connection,
        ), patch(
            "backend.management.commands.rebuild_index.Command.index_managers",
            {
                "MOCK_MANAGER": self.mock_manager,
            },
        ), patch.object(
            self.mock_manager, "rebuild", return_value=None
        ):
            # This should return manager.rebuild() which should be none for this test case
            assert self.call_command(index_name="MOCK_MANAGER") is None

    def test_invalid_index_provided(self, caplog):
        with patch(
            "elasticsearch.dsl.connections.Connections.get_connection",
            return_value=self.mock_connection,
        ), patch(
            "backend.management.commands.rebuild_index.Command.index_managers",
            {
                "MOCK_MANAGER": self.mock_manager,
            },
        ):
            self.call_command("--index", "invalid_key")

        assert not self.mock_manager.rebuild.called

        assert (
            "Can't rebuild index for unrecognized alias: [invalid_key]" in caplog.text
        )
