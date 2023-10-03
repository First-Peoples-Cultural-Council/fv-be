import json
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
            new_lyric_text = extract_plain_text(json.loads(lyric.text))
            lyric.text = new_lyric_text
            lyric.save()
        except JSONDecodeError:
            continue

    for lyric in lyric_translation_list:
        try:
            new_lyric_translation = extract_plain_text(json.loads(lyric.translation))
            lyric.translation = new_lyric_translation
            lyric.save()
        except JSONDecodeError:
            continue


def extract_plain_text(draftjs):
    plain_text = ""
    for index, block in enumerate(draftjs["blocks"]):
        if block["text"] != "":
            plain_text += block["text"]
        if index != len(draftjs["blocks"]) - 1:
            plain_text += delimiter
    return plain_text
