import logging
from datetime import datetime, timedelta

from celery import current_task, shared_task
from django.db.models import Q
from django.db.models.query import QuerySet
from mothertongues.config.models import DataSource
from mothertongues.config.models import DictionaryEntry as MTDictionaryEntry
from mothertongues.config.models import (
    LanguageConfiguration,
    MTDConfiguration,
    ResourceManifest,
    RestrictedTransducer,
)
from mothertongues.dictionary import MTDictionary

from backend.models import DictionaryEntry, MTDExportFormat, Site, constants
from backend.models.dictionary import DictionaryEntryCategory
from backend.serializers.site_data_serializers import DictionaryEntryDataSerializer
from firstvoices.celery import link_error_handler

LOGGER = logging.getLogger(__name__)


def parse_queryset_for_mtd(
    dictionary_entries_queryset: QuerySet | list[DictionaryEntry],
):
    entries = []
    for entry in dictionary_entries_queryset:
        try:
            parsed_entry = MTDictionaryEntry(
                entryID=str(entry.id),
                word=entry.title,
                definition=DictionaryEntryDataSerializer.get_definition(entry),
                sorting_form=DictionaryEntryDataSerializer.get_sorting_form(entry),
                source=DictionaryEntryDataSerializer.get_source(entry),
                audio=DictionaryEntryDataSerializer.get_audio(entry),
                video=DictionaryEntryDataSerializer.get_video(entry),
                img=DictionaryEntryDataSerializer.get_img(entry),
                theme=DictionaryEntryDataSerializer.get_theme(entry),
                secondary_theme=DictionaryEntryDataSerializer.get_secondary_theme(
                    entry
                ),
                optional=DictionaryEntryDataSerializer.get_optional(entry),
            )
        except ValueError as e:
            LOGGER.warning(
                f"Entry with ID {entry.id} did not pass Validation. Instead raised: {e}"
            )
            continue
        entries.append(parsed_entry)
    return entries


@shared_task
def build_index_and_calculate_scores(site_or_site_slug: str | Site, *args, **kwargs):
    """This task builds the inverted index and calculates the entry rankings

    Args:
        site_slug (Union[str, Site]): A valid site slug or a backend.models.Site object
    """
    if isinstance(site_or_site_slug, Site):
        site = site_or_site_slug
    elif isinstance(site_or_site_slug, str):
        site = Site.objects.get(slug=site_or_site_slug)
    else:
        raise TypeError(
            f"""site_or_site_slug must be a backend.models.Site object or a valid site slug.
                {type(site_or_site_slug)} was received instead."""
        )
    characters_list = site.character_set.all().order_by("sort_order")
    dictionary_entries = parse_queryset_for_mtd(
        DictionaryEntry.objects.filter(
            site=site, visibility=constants.Visibility.PUBLIC
        )
    )
    preview = {}
    task_id = current_task.request.id
    # Saving an empty row to depict that the task has started
    MTDExportFormat.objects.create(
        site=site,
        latest_export_result=preview,
        task_id=task_id,
        is_preview=True,
    )
    # Normalization transducers can be defined to:
    #       - apply lower casing
    #       - apply unicode normalization
    #       - remove punctuation
    #       - remove combining characters (currently removes everything between \u0300 and \u036f)
    #       - apply arbitrary replace rules (with replace_rules key)
    # All of these processes get applied to the dictionary terms before indexing and scoring.
    # The configuration is exported as part of the MTD export format so that the exact same
    # normalization processes are also applied to every term in the search query on the front end
    # in order to ensure normalization between search terms and index terms
    l1_normalization_transducer = RestrictedTransducer(
        lower=True,
        unicode_normalization="NFC",
        remove_punctuation="[.,/#!$%^&?*';:{}=\\-_`~()]",
        remove_combining_characters=True,
    )
    # NOTE: We might want to save these LanguageConfigurations elsewhere
    #       when we decide to customize
    #       the search algorithms. They can
    #       be serialized with the export method (config.export()).
    config = LanguageConfiguration(
        L1=None if site is None else site.title,
        L2="English",
        alphabet=[character.title for character in characters_list],
        build=datetime.now().strftime("%Y%m%d%H%M"),
        l1_normalization_transducer=l1_normalization_transducer,
    )
    mtd_config = MTDConfiguration(
        config=config,
        data=DataSource(
            manifest=ResourceManifest(name=site.title), resource=dictionary_entries
        ),
    )
    # NOTE: I've set sort_data=False, but this assumes that the sorting is done elsewhere
    #       and that each entry will have a `sorting_form` field.
    #       If we want to add custom sorting back in using MTD, just set it to True again
    #       and ensure that the language configuration includes the correct alphabet.
    dictionary = MTDictionary(mtd_config, sort_data=False)
    if dictionary.data and len(dictionary) > 0:
        dictionary.build_indices()
    preview = dictionary.export().model_dump(mode="json")

    # Save the new result to the database
    new_result = MTDExportFormat.objects.create(
        site=site,
        latest_export_result=preview,
        task_id=task_id,
        is_preview=False,
    )

    # Delete any previous results and previews
    MTDExportFormat.objects.filter(site=site).exclude(id=new_result.id).delete()

    return preview


@shared_task
def check_sites_for_mtd_sync():
    sites = Site.objects.all()
    six_hours_ago = datetime.now() - timedelta(hours=6)

    for site in sites:
        updated_entries_count = DictionaryEntry.objects.filter(
            site=site, last_modified__gte=six_hours_ago
        ).count()

        updated_categories_count = DictionaryEntryCategory.objects.filter(
            category__site=site, last_modified__gte=six_hours_ago
        ).count()

        updated_related_media_count = (
            DictionaryEntry.objects.filter(site=site)
            .filter(
                Q(related_audio__last_modified__gte=six_hours_ago)
                | Q(related_images__last_modified__gte=six_hours_ago)
                | Q(related_videos__last_modified__gte=six_hours_ago)
            )
            .distinct()
            .count()
        )

        relevant_changes_count = (
            updated_entries_count
            + updated_categories_count
            + updated_related_media_count
        )

        if relevant_changes_count > 0:
            build_index_and_calculate_scores.apply_async(
                (site,),
                link_error=link_error_handler.s(),
            )
            LOGGER.info(f"MTD Index for site {site.slug} has been updated.")
