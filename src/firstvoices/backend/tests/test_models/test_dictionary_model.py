import pytest
from django.core.management import call_command

from firstvoices.backend.models.characters import Alphabet
from firstvoices.backend.tests.factories import (
    AlphabetFactory,
    ControlledSiteContentFactory,
    SiteFactory,
)


class TestDictionarySortProcessing:
    @pytest.fixture
    def g2p_db_setup(self, django_db_blocker):
        with django_db_blocker.unblock():
            call_command("loaddata", "default_g2p_config.json")

    @pytest.mark.django_db
    def test_autocreate_alphabet_on_save(self, g2p_db_setup):
        """When no alphabet exists, creating sortable content should create it"""
        site = SiteFactory.create()
        assert len(Alphabet.objects.filter(site_id=site.id)) == 0
        ControlledSiteContentFactory.create(site=site)
        assert len(Alphabet.objects.filter(site_id=site.id)) == 1

    @pytest.mark.django_db
    def test_custom_sort_on_save(self, g2p_db_setup):
        """Saving sortable content should reapply sort"""
        alphabet = AlphabetFactory.create()
        content = ControlledSiteContentFactory.create(
            site=alphabet.site, title="qwerty", custom_order="x"
        )
        assert content.custom_order == alphabet.get_custom_order(content.title)

    @pytest.mark.django_db
    def test_clean_confusables_on_save(self, g2p_db_setup):
        """Saving sortable content should clean confusables"""
        alphabet = AlphabetFactory.create(
            input_to_canonical_map=[
                {"in": "old", "out": "new"},
            ],
        )
        title = "old-old"
        content = ControlledSiteContentFactory.create(site=alphabet.site, title=title)
        assert content.title != title
        assert content.title == alphabet.clean_confusables(title)
