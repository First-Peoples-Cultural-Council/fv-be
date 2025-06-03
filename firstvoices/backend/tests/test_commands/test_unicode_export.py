import json
import os
import shutil

import pytest
from django.core.management import call_command

from backend.models import Language
from backend.models.constants import Visibility
from backend.tests import factories


@pytest.fixture
def get_tmp_output_dir(request) -> str:
    output_dir = os.path.join(os.getcwd(), "output")

    # Function to clear the resources
    def remove_output():
        shutil.rmtree(output_dir, ignore_errors=True)

    request.addfinalizer(remove_output)

    return output_dir


@pytest.mark.django_db
class TestUnicodeExport:
    def test_subfolders_for_all_sites(self, get_tmp_output_dir):
        language = Language.objects.first()
        site1 = factories.SiteFactory.create(
            slug="site1", language=language, visibility=Visibility.TEAM
        )
        site2 = factories.SiteFactory.create(slug="site2", visibility=Visibility.TEAM)
        site3 = factories.SiteFactory.create(
            slug="site3", language=language, visibility=Visibility.MEMBERS
        )
        site4 = factories.SiteFactory.create(
            slug="site4", language=language, visibility=Visibility.PUBLIC
        )

        call_command("unicode_export")
        assert not os.path.exists(os.path.join(get_tmp_output_dir, site1.slug))
        assert not os.path.exists(os.path.join(get_tmp_output_dir, site2.slug))
        assert os.path.exists(os.path.join(get_tmp_output_dir, site3.slug))
        assert os.path.exists(os.path.join(get_tmp_output_dir, site4.slug))

    def test_language_metadata(self, get_tmp_output_dir):
        call_command("unicode_export")

        filename = os.path.join(get_tmp_output_dir, "bc_language_metadata_2025.csv")
        assert os.path.exists(filename)

        language = Language.objects.get(title="Anishinaabemowin")

        with open(filename) as f:
            header = f.readline()
            assert (
                header
                == "Language ID,Language Name,Alternate Names,Keywords for Communities Where Language is Spoken,"
                "BCP 47 Language Code\n"
            )
            firstline = f.readline()
            assert (
                firstline
                == f'"{language.id}","Anishinaabemowin","Saulteau, Saulteaux, Ojibwe, Ojibway, Ojibwa, Plains '
                f'Ojibway","","oji"\n'
            )

    def test_site_metadata(self, get_tmp_output_dir):
        language = Language.objects.first()
        factories.SiteFactory.create(
            slug="site1", language=language, visibility=Visibility.TEAM
        )
        factories.SiteFactory.create(slug="site2", visibility=Visibility.TEAM)
        site3 = factories.SiteFactory.create(
            slug="site3",
            title="Site 3",
            language=language,
            visibility=Visibility.MEMBERS,
        )

        call_command("unicode_export")
        filename = os.path.join(
            get_tmp_output_dir, "firstvoices_sites_metadata_2025.csv"
        )
        assert os.path.exists(filename)

        with open(filename) as f:
            header = f.readline()
            assert (
                header
                == "Site ID,Slug,FirstVoices Site Name,URL,Language Name,Language ID\n"
            )

            firstline = f.readline()
            assert (
                firstline
                == f'"{site3.id}","site3","Site 3","https://firstvoices.com/site3","{site3.language.title}",'
                f'"{site3.language.id}"\n'
            )

    def test_alphabet_ordering(self, get_tmp_output_dir):
        language = Language.objects.first()
        site = factories.SiteFactory.create(
            slug="sluggo", language=language, visibility=Visibility.MEMBERS
        )
        char3 = factories.CharacterFactory.create(site=site, sort_order=3, title="C")
        char1 = factories.CharacterFactory.create(
            site=site, sort_order=1, title="A", approximate_form="a"
        )

        call_command("unicode_export")

        filename = os.path.join(get_tmp_output_dir, site.slug, "alphabet_ordering.csv")
        assert os.path.exists(filename)

        with open(filename) as f:
            header = f.readline()
            assert header == "Sort Order,Character,Approximate Latin Form(s)\n"

            line = f.readline()
            assert (
                line
                == f'"{char1.sort_order}","{char1.title}","{char1.approximate_form}"\n'
            )
            line = f.readline()
            assert line == f'"{char3.sort_order}","{char3.title}",""\n'

    def test_character_variants(self, get_tmp_output_dir):
        language = Language.objects.first()
        site = factories.SiteFactory.create(
            language=language, visibility=Visibility.MEMBERS
        )
        char3 = factories.CharacterFactory.create(site=site, sort_order=3, title="C")
        var3 = factories.CharacterVariantFactory.create(
            site=site, base_character=char3, title="Cc"
        )
        char1 = factories.CharacterFactory.create(
            site=site, sort_order=1, title="A", approximate_form="a"
        )
        var1 = factories.CharacterVariantFactory.create(
            site=site, base_character=char1, title="Aa"
        )

        call_command("unicode_export")

        filename = os.path.join(get_tmp_output_dir, site.slug, "character_variants.csv")
        assert os.path.exists(filename)

        with open(filename) as f:
            header = f.readline()
            assert header == "Base Character,Variant\n"

            line = f.readline()
            assert line == f'"{char1.title}","{var1.title}"\n'
            line = f.readline()
            assert line == f'"{char3.title}","{var3.title}"\n'

    def test_ignored_characters(self, get_tmp_output_dir):
        language = Language.objects.first()
        site = factories.SiteFactory.create(
            language=language, visibility=Visibility.MEMBERS
        )
        ignored1 = factories.IgnoredCharacterFactory.create(site=site, title="-")
        ignored2 = factories.IgnoredCharacterFactory.create(site=site, title="/")

        call_command("unicode_export")

        filename = os.path.join(get_tmp_output_dir, site.slug, "ignored_characters.csv")
        assert os.path.exists(filename)

        with open(filename) as f:
            header = f.readline()
            assert header == "Ignored Character\n"

            line = f.readline()
            assert line == f'"{ignored1.title}"\n'
            line = f.readline()
            assert line == f'"{ignored2.title}"\n'

    def test_confusable_characters(self, get_tmp_output_dir):
        language = Language.objects.first()
        site = factories.SiteFactory.create(
            language=language, visibility=Visibility.MEMBERS
        )
        confusables_map = json.loads(
            '[{"in": "k̒ʷ", "out": "k̓ʷ"}, {"in": "k̍ʷ", "out": "k̓ʷ"}]'
        )
        factories.AlphabetFactory.create(
            site=site, input_to_canonical_map=confusables_map
        )

        call_command("unicode_export")

        filename = os.path.join(
            get_tmp_output_dir, site.slug, "confusable_characters.csv"
        )
        assert os.path.exists(filename)

        with open(filename) as f:
            header = f.readline()
            assert header == "Confusable,Canonical Character\n"

            line = f.readline()
            assert line == '"k̒ʷ","k̓ʷ"\n'

    def test_empty_site_has_no_files(self, get_tmp_output_dir):
        language = Language.objects.first()
        site = factories.SiteFactory.create(
            language=language, visibility=Visibility.MEMBERS
        )

        call_command("unicode_export")

        subfolder = os.path.join(get_tmp_output_dir, site.slug)
        assert os.path.exists(os.path.join(subfolder))
        assert not os.path.exists(os.path.join(subfolder, "alphabet_ordering.csv"))
        assert not os.path.exists(os.path.join(subfolder, "character_variants.csv"))
        assert not os.path.exists(os.path.join(subfolder, "ignored_characters.csv"))
        assert not os.path.exists(os.path.join(subfolder, "confusable_characters.csv"))

    def test_empty_confusables(self, get_tmp_output_dir):
        language = Language.objects.first()
        site = factories.SiteFactory.create(
            language=language, visibility=Visibility.MEMBERS
        )
        factories.AlphabetFactory.create(site=site)

        call_command("unicode_export")

        subfolder = os.path.join(get_tmp_output_dir, site.slug)
        assert os.path.exists(os.path.join(subfolder))
        assert not os.path.exists(os.path.join(subfolder, "confusable_characters.csv"))
