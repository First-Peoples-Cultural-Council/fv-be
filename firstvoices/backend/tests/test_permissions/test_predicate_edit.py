import pytest

from backend.models.constants import AppRole
from backend.permissions.predicates import edit
from backend.tests.factories import SiteFactory, get_app_admin


class TestEditRolePredicates:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "predicate",
        [
            edit.is_at_least_assistant_or_super,
            edit.is_at_least_editor_or_super,
            edit.is_language_admin_or_super,
        ],
    )
    def test_superadmin_can_edit(self, predicate):
        user = get_app_admin(AppRole.SUPERADMIN)
        obj = SiteFactory.create()
        assert predicate(user, obj)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "predicate",
        [
            edit.is_at_least_assistant_or_super,
            edit.is_at_least_editor_or_super,
            edit.is_language_admin_or_super,
        ],
    )
    def test_staff_admin_can_not_edit(self, predicate):
        user = get_app_admin(AppRole.STAFF)
        obj = SiteFactory.create()
        assert not predicate(user, obj)
