import pytest
from django.db.utils import IntegrityError

from backend.tests.factories import ImmersionLabelFactory


class TestImmersionLabelModel:
    @pytest.mark.django_db
    def test_immersion_lable_unique_key(self):
        """Immersion label can't be created with the same key and site as another"""
        immersion_label = ImmersionLabelFactory.create()
        with pytest.raises(IntegrityError):
            ImmersionLabelFactory.create(
                site=immersion_label.site, key=immersion_label.key
            )
