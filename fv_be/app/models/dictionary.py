from django.db import models


class Note(models.Model):
    """Model for notes associated to each dictionary entry."""

    # from fv:notes,fv:general_note, fv:cultural_note, fv:literal_translation, fv-word:notes, fv-phrase:notes
    text = models.TextField()


class Acknowledgment(models.Model):
    """Model for acknowledgments associated to each dictionary entry."""

    # from fv:acknowledgments, fv:source, fv:reference, fv-word:acknowledgement, fv-phrase:acknowledgement
    text = models.TextField()


class Translation(models.Model):
    """Model for translations associated to each dictionary entry."""

    # Choices for Language
    ENGLISH_ENUM_KEY = "EN"
    FRENCH_ENUM_KEY = "FR"
    LANGUAGE_CHOICES = [(ENGLISH_ENUM_KEY, "English"), (FRENCH_ENUM_KEY, "French")]

    # Fields
    translation = models.CharField(max_length=200)
    language = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, default=ENGLISH_ENUM_KEY
    )
    # todo: connect to parts of speech
    # from fv-word:part_of_speech
    # part_of_speech =
    # todo: the following attribute's name
    parent = models.ForeignKey("DictionaryEntry", on_delete=models.CASCADE)


class AlternateSpelling(models.Model):
    """Model for alternate spellings associated to each dictionary entry."""

    # todo: more representative name for the following attribute ?
    # from fv:alternate_spelling, fv-word:alternate_spellings, fv-phrase:alternate_spellings
    text = models.CharField(max_length=200)
    # todo: the following attribute's name
    parent = models.ForeignKey("DictionaryEntry", on_delete=models.CASCADE)


class Pronunciation(models.Model):
    """Model for pronunciations associated to each dictionary entry."""

    # todo: more representative name for the following attribute ?
    # from fv-word:pronunciation
    text = models.CharField(max_length=200)
    # todo: the following attribute's name
    parent = models.ForeignKey("DictionaryEntry", on_delete=models.CASCADE)


class DictionaryEntry(models.Model):
    """Model for dictionary entries"""

    class Meta:
        verbose_name_plural = "DictionaryEntries"

    # Choices for Type
    WORD_ENUM_KEY = "WORD"
    PHRASE_ENUM_KEY = "PHRASE"
    TYPE_OF_ENTRY_CHOICES = [(WORD_ENUM_KEY, "Word"), (PHRASE_ENUM_KEY, "Phrase")]

    # Fields
    # from dc:title
    title = models.CharField(max_length=200)
    type = models.CharField(
        max_length=6, choices=TYPE_OF_ENTRY_CHOICES, default=WORD_ENUM_KEY
    )
    # todo: Link to site model when available
    # may be inherited from an abstract base class or mixin later
    # site = models.ForeignKey(
    #     'Site',
    #     on_delete=models.CASCADE
    # )
    notes = models.ForeignKey("Note", on_delete=models.SET_NULL, null=True)
    acknowledgments = models.ForeignKey(
        "Acknowledgment", on_delete=models.SET_NULL, null=True
    )
    # todo: Add categories table
    # from fv-word:categories, fv-phrase:phrase_books
    # categories =
    # from fv:custom_order
    custom_order = models.CharField(max_length=200, blank=True)
    # from fv-word:available_in_games, fvaudience:games
    exclude_from_games = models.BooleanField(default=False)
    # from fvaudience:children fv:available_in_childrens_archive
    # exclude_from_kids can be a shared mixin for dictionary_entries, songs, stories and media
    exclude_from_kids = models.BooleanField(default=False)
    batch_id = models.CharField(max_length=255, blank=True)
    # from fv:related_assets, fv-word:related_phrases
    related_dictionary_entries = models.ManyToManyField("self")
