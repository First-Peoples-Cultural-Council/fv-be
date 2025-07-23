import logging
from datetime import datetime

from celery import current_task, shared_task
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.db.models.query import Prefetch, QuerySet
from django.utils import timezone
from mothertongues.config.models import DataSource
from mothertongues.config.models import DictionaryEntry as MTDictionaryEntry
from mothertongues.config.models import (
    LanguageConfiguration,
    MTDConfiguration,
    ResourceManifest,
    RestrictedTransducer,
)
from mothertongues.dictionary import MTDictionary

from backend.models import Category, DictionaryEntry, MTDExportJob, Site, constants
from backend.models.dictionary import DictionaryEntryCategory
from backend.models.jobs import JobStatus
from backend.models.media import Audio, Image, Video
from backend.serializers.site_data_serializers import DictionaryEntryDataSerializer
from backend.tasks.utils import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE
from firstvoices.celery import link_error_handler


def parse_queryset_for_mtd(
    dictionary_entries_queryset: QuerySet | list[DictionaryEntry],
):
    logger = logging.getLogger(__name__)
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
            logger.info(
                f"Entry with ID {entry.id} did not pass Validation. Instead raised: {e}"
            )
            continue
        entries.append(parsed_entry)
    return entries


@shared_task
def build_index_and_calculate_scores(site_slug: str, *args, **kwargs):
    """This task builds the inverted index and calculates the entry rankings

    Args:
        site_slug (str): A valid site slug
    """
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE, f"site: {site_slug}")

    if isinstance(site_slug, str):
        site = Site.objects.get(slug=site_slug)
    else:
        raise TypeError(
            f"""site_or_site_slug must be a backend.models.Site object or a valid site slug.
                {type(site_slug)} was received instead."""
        )

    # Saving an empty model to depict that the task has started
    export_job = MTDExportJob.objects.create(
        site=site,
        export_result={},
        task_id=current_task.request.id,
        status=JobStatus.STARTED,
    )

    if (
        MTDExportJob.objects.filter(status=JobStatus.STARTED, site=site)
        .exclude(id=export_job.id)
        .exists()
    ):
        cancelled_message = "Job cancelled as another MTD export job is already in progress for the same site."
        export_job.status = JobStatus.CANCELLED
        export_job.message = cancelled_message
        export_job.save()
        logger.info(cancelled_message)
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return export_job.id

    characters_list = site.character_set.all().order_by("sort_order")
    dictionary_entries_queryset = (
        DictionaryEntry.objects.filter(
            site=site, visibility=constants.Visibility.PUBLIC, translations__len__gt=0
        )
        .select_related("part_of_speech")
        .prefetch_related(
            "site__alphabet_set",
            Prefetch(
                "categories",
                queryset=Category.objects.all().select_related("parent"),
            ),
            Prefetch(
                "related_audio",
                queryset=Audio.objects.all()
                .select_related("original")
                .prefetch_related("speakers"),
            ),
            Prefetch(
                "related_images",
                queryset=Image.objects.all().select_related("original"),
            ),
            Prefetch(
                "related_videos",
                queryset=Video.objects.all().select_related("original"),
            ),
        )
        .defer(
            "exclude_from_wotd",
            "legacy_batch_filename",
            "related_dictionary_entries",
            "related_characters",
            "custom_order",
            "split_chars_base",
            "alternate_spellings",
            "pronunciations",
        )
    )
    dictionary_entries = parse_queryset_for_mtd(dictionary_entries_queryset)

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
        try:
            dictionary.build_indices()
        except Exception as e:
            export_job.status = JobStatus.FAILED
            export_job.message = str(e)
            export_job.save()
            logger.error(e)
            logger.info(ASYNC_TASK_END_TEMPLATE)
            return export_job.id
    result = dictionary.export().model_dump(mode="json")

    # Save the new result to the database
    export_job.export_result = result
    export_job.status = JobStatus.COMPLETE
    export_job.save()

    # Delete any previous results for the same site
    MTDExportJob.objects.filter(site=site).exclude(id=export_job.id).delete()

    logger.info(ASYNC_TASK_END_TEMPLATE)

    return export_job.id


@shared_task(bind=True)
def check_sites_for_mtd_sync(self):
    logger = get_task_logger(__name__)
    logger.info(ASYNC_TASK_START_TEMPLATE)

    try:
        sites = Site.objects.filter(visibility=constants.Visibility.PUBLIC)

        for site in sites:
            completed_jobs = MTDExportJob.objects.filter(
                site=site, status=JobStatus.COMPLETE
            )
            if completed_jobs.exists():
                last_export = completed_jobs.latest()
                last_export_created = last_export.created
                logger.info(
                    f"Checking for MTD changes on site {site.title} since {last_export_created}. "
                    f"Current time: {timezone.now()}"
                )

                updated_entries_count = DictionaryEntry.objects.filter(
                    site=site, system_last_modified__gte=last_export_created
                ).count()

                updated_categories_count = DictionaryEntryCategory.objects.filter(
                    category__site=site, system_last_modified__gte=last_export_created
                ).count()

                updated_related_media_count = (
                    DictionaryEntry.objects.filter(site=site)
                    .filter(
                        Q(related_audio__system_last_modified__gte=last_export_created)
                        | Q(
                            related_images__system_last_modified__gte=last_export_created
                        )
                        | Q(
                            related_videos__system_last_modified__gte=last_export_created
                        )
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
                    logger.info(f"Starting MTD Index update for site {site.slug}.")
                    build_index_and_calculate_scores.apply_async(
                        (site.slug,),
                        link_error=link_error_handler.s(),
                    )
            else:
                logger.info(f"Starting MTD Index build for site {site.slug}.")
                build_index_and_calculate_scores.apply_async(
                    (site.slug,),
                    link_error=link_error_handler.s(),
                )

        logger.info(ASYNC_TASK_END_TEMPLATE)

    except Exception as e:
        self.state = "FAILURE"
        logger.error(f"MTD Sync check failed: {e}")
        logger.info(ASYNC_TASK_END_TEMPLATE)
        raise e
