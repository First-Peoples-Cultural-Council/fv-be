import json
import os

from django.core.management import BaseCommand

from backend.models import Character, CharacterVariant, IgnoredCharacter, Language, Site
from backend.models.constants import Visibility


class Command(BaseCommand):
    help = "Export unicode information for all sites, suitable for publishing in the unicode-resources repo."

    def handle(self, *args, **options):
        """
        Export unicode information for all sites, suitable for publishing in the unicode-resources repo. Files will
        be output to `./output`.

        Run with:
        python manage.py unicode_export

        """
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)

        self.export_language_metadata(output_dir)

        sites = self.get_published_bc_language_sites()
        self.export_sites_metadata(output_dir, sites)

        for s in sites:
            self.export_site_unicode_folder(output_dir, s)

    def get_published_bc_language_sites(self):
        return (
            Site.objects.all()
            .filter(language__isnull=False)
            .filter(visibility__in=[Visibility.MEMBERS, Visibility.PUBLIC])
            .order_by("slug")
        )

    def export_language_metadata(self, output_dir):
        languages = Language.objects.all().order_by("title")

        filename = os.path.join(output_dir, "bc_language_metadata_2025.csv")

        with open(filename, "w") as f:
            f.write(
                "Language ID,Language Name,Alternate Names,Keywords for Communities Where Language is Spoken,"
                "BCP 47 Language Code\n"
            )

            for lang in languages:
                f.write(
                    f'"{lang.id}","{lang.title}","{lang.alternate_names}","{lang.community_keywords}",'
                    f'"{lang.language_code}"\n'
                )

    def export_sites_metadata(self, output_dir, sites):
        # Non-BC languages are not associated with a Language
        # Exclude Team-only sites

        fv_url = "https://firstvoices.com/"

        filename = os.path.join(output_dir, "firstvoices_sites_metadata_2025.csv")

        with open(filename, "w") as f:
            f.write(
                "Site ID,Slug,FirstVoices Site Name,URL,Language Name,Language ID\n"
            )

            for s in sites:
                f.write(
                    f'"{s.id}","{s.slug}","{s.title}","{fv_url}{s.slug}","{s.language.title}","{s.language.id}"\n'
                )

    def export_site_unicode_folder(self, output_dir, site):
        output_subfolder = self.create_site_subfolder(output_dir, site)

        self.export_alphabet(output_subfolder, site)
        self.export_character_variants(output_subfolder, site)
        self.export_ignored_characters(output_subfolder, site)
        self.export_confusable_characters(output_subfolder, site)

    def create_site_subfolder(self, output_dir, site):
        subfolder = os.path.join(output_dir, site.slug)
        os.makedirs(subfolder, exist_ok=True)
        return subfolder

    def export_alphabet(self, output_dir, site):
        characters = Character.objects.all().filter(site=site).order_by("sort_order")
        if characters.count() == 0:
            return

        filename = os.path.join(output_dir, "alphabet_ordering.csv")
        with open(filename, "w") as f:
            f.write("Sort Order,Character,Approximate Latin Form(s)\n")

            for c in characters:
                f.write(f'"{c.sort_order}","{c.title}","{c.approximate_form}"\n')

    def export_character_variants(self, output_dir, site):
        variants = (
            CharacterVariant.objects.all()
            .filter(site=site)
            .order_by("base_character__sort_order")
        )
        if variants.count() == 0:
            return

        filename = os.path.join(output_dir, "character_variants.csv")
        with open(filename, "w") as f:
            f.write("Base Character,Variant\n")

            for v in variants:
                f.write(f'"{v.base_character.title}","{v.title}"\n')

    def export_ignored_characters(self, output_dir, site):
        ignoreds = IgnoredCharacter.objects.all().filter(site=site).order_by("created")
        if ignoreds.count() == 0:
            return

        filename = os.path.join(output_dir, "ignored_characters.csv")
        with open(filename, "w") as f:
            f.write("Ignored Character\n")

            for i in ignoreds:
                f.write(f'"{i.title}"\n')

    def export_confusable_characters(self, output_dir, site):
        alphabet = site.alphabet_set.first()
        if alphabet is None:
            return

        confusables = json.loads(alphabet.input_to_canonical_map)

        filename = os.path.join(output_dir, "confusable_characters.csv")
        with open(filename, "w") as f:
            f.write("Confusable,Canonical Character\n")

            for c in confusables:
                f.write(f"\"{c['in']}\",\"{c['out']}\"\n")
