import json
import logging
from json import JSONDecodeError

from django.core.management import BaseCommand

from backend.models import Lyric

delimiter = "\n"


class Command(BaseCommand):
    def handle(self, **options):
        lyric_draftjs_to_text()


def lyric_draftjs_to_text():
    lyric_text_list = Lyric.objects.exclude(text__exact="")
    lyric_translation_list = Lyric.objects.exclude(translation__exact="")

    for lyric in lyric_text_list:
        try:
            new_lyric_text = extract_plain_text(json.loads(lyric.text), lyric.id)
            if new_lyric_text is not None:
                lyric.text = new_lyric_text
                lyric.save()
        except JSONDecodeError:
            continue

    for lyric in lyric_translation_list:
        try:
            new_lyric_translation = extract_plain_text(json.loads(lyric.translation))
            if new_lyric_translation is not None:
                lyric.translation = new_lyric_translation
                lyric.save()
        except JSONDecodeError:
            continue


def extract_plain_text(draftjs, lyric_id=None):
    logger = logging.getLogger(__name__)
    if "blocks" in draftjs:
        return delimiter.join([block["text"] for block in draftjs["blocks"]])
    else:
        logger.warning(
            f"No blocks found in draftjs for lyric with ID {lyric_id} when converting draftjs to text."
        )
        return None
