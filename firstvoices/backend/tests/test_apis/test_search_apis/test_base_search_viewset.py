from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.tests.test_apis.test_search_apis.base_search_test import SearchMocksMixin
from backend.views.base_search_views import BaseSearchViewSet


class MinimalSerializer(serializers.Serializer):
    """A test serializer with no make_queryset_eager function"""

    id = serializers.UUIDField()


class EagerSerializer(serializers.Serializer):
    """A test serializer that does support make_queryset_eager"""

    id = serializers.UUIDField()
    title = serializers.CharField()

    @classmethod
    def make_queryset_eager(cls, queryset):
        return queryset


class TestBaseSearchViewSet(SearchMocksMixin):
    @pytest.mark.parametrize("query", [{}, {"query": "   "}])
    def test_get_search_params_empty(self, query):
        mock_request = self.create_mock_request(user=AnonymousUser(), query_dict=query)
        viewset = BaseSearchViewSet()
        viewset.request = mock_request

        actual = viewset.get_search_params()

        assert actual == {"q": "", "user": AnonymousUser()}

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("test", "test"),
            (" test ", "test"),
            (" test", "test"),
            ("test ", "test"),
            (" a b c ", "a b c"),
            (
                "a valid query **with $@&*456ŧ specials!",
                "a valid query **with $@&*456ŧ specials!",
            ),
            ("Ⱥ Ṁixed Ćase Query", "ⱥ ṁixed ćase query"),
            ("ááááá", "ááááá"),  # nfc normalization
        ],
    )
    def test_get_search_params_q(self, input, expected):
        query = {"q": input}
        mock_request = self.create_mock_request(
            user=factories.get_anonymous_user(), query_dict=query
        )
        viewset = BaseSearchViewSet()
        viewset.request = mock_request

        actual = viewset.get_search_params()

        assert actual["q"] == expected

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "user_factory", [factories.get_anonymous_user, factories.get_non_member_user]
    )
    def test_get_search_params_user(self, user_factory):
        query = {"q": ""}
        user = user_factory()
        mock_request = self.create_mock_request(user=user, query_dict=query)
        viewset = BaseSearchViewSet()
        viewset.request = mock_request

        actual = viewset.get_search_params()

        assert actual["user"] == user

    def test_get_pagination_params_empty(self):
        params = {}
        mock_request = self.create_mock_request(user=AnonymousUser(), query_dict=params)
        viewset = BaseSearchViewSet()
        viewset.request = mock_request

        actual = viewset.get_pagination_params()

        assert actual == {
            "page": 1,
            "start": 0,
            "page_size": 25,
        }

    @pytest.mark.parametrize(
        "params",
        [
            {"pageSize": "zebra"},
            {"page": "-10"},
            {"page": "true"},
            {"PAGE": "3", "PAGESIZE": "10"},
        ],
        ids=["string", "negative", "boolean", "all_caps"],
    )
    def test_get_pagination_params_invalid(self, params):
        mock_request = self.create_mock_request(user=AnonymousUser(), query_dict=params)
        viewset = BaseSearchViewSet()
        viewset.request = mock_request

        actual = viewset.get_pagination_params()

        assert actual == {
            "page": 1,
            "start": 0,
            "page_size": 25,
        }

    @pytest.mark.parametrize("params", [{"page": "3", "pageSize": "10"}])
    def test_get_pagination_params_valid(self, params):
        mock_request = self.create_mock_request(user=AnonymousUser(), query_dict=params)
        viewset = BaseSearchViewSet()
        viewset.request = mock_request

        actual = viewset.get_pagination_params()

        assert actual == {
            "page": 3,
            "start": 20,
            "page_size": 10,
        }

    def test_hydrate_empty_results(self):
        mock_search_results = []
        viewset = BaseSearchViewSet()
        actual = viewset.hydrate(mock_search_results)
        assert actual == {}

    @pytest.mark.django_db
    def test_hydrate_one_result(self):
        model = factories.SongFactory.create()
        mock_search_results = [self.get_song_search_result(model)]

        viewset = BaseSearchViewSet()
        viewset.serializer_class = MinimalSerializer

        actual = viewset.hydrate(mock_search_results)

        assert actual == {"Song": {str(model.id): model}}

    @pytest.mark.django_db
    def test_hydrate_multiple_serializers(self):
        song = factories.SongFactory.create()
        word = factories.DictionaryEntryFactory.create(type=TypeOfDictionaryEntry.WORD)
        mock_search_results = [
            self.get_song_search_result(song),
            self.get_dictionary_search_result(word),
        ]

        viewset = BaseSearchViewSet()
        viewset.serializer_classes = {
            "Song": MinimalSerializer,
            "DictionaryEntry": EagerSerializer,
        }

        actual = viewset.hydrate(mock_search_results)

        assert actual == {
            "Song": {str(song.id): song},
            "DictionaryEntry": {str(word.id): word},
        }

    @pytest.mark.django_db
    def test_hydrate_missing_data(self):
        mock_search_results = [
            self.get_song_search_result(),
            self.get_dictionary_search_result(),
        ]

        viewset = BaseSearchViewSet()
        viewset.serializer_classes = {
            "Song": MinimalSerializer,
            "DictionaryEntry": EagerSerializer,
        }

        actual = viewset.hydrate(mock_search_results)

        assert actual == {"DictionaryEntry": {}, "Song": {}}

    def test_serialize_search_results_empty(self):
        mock_search_results = []
        mock_data = {"DictionaryEntry": {}, "Song": {}}

        viewset = BaseSearchViewSet()
        viewset.serializer_classes = {
            "Song": MinimalSerializer,
            "DictionaryEntry": EagerSerializer,
        }

        actual = viewset.serialize_search_results(mock_search_results, mock_data)
        assert actual == []

    @pytest.mark.django_db
    def test_serialize_search_results_one(self):
        song = factories.SongFactory.create()
        mock_search_results = [self.get_song_search_result(song)]
        mock_data = {"Song": {str(song.id): song}}

        viewset = BaseSearchViewSet()
        viewset.request = MagicMock()
        viewset.format_kwarg = MagicMock()
        viewset.serializer_classes = {
            "Song": MinimalSerializer,
        }

        actual = viewset.serialize_search_results(mock_search_results, mock_data)
        assert actual == [{"id": str(song.id)}]

    @pytest.mark.django_db
    def test_serialize_search_results_multiple(self):
        song = factories.SongFactory.create()
        word = factories.DictionaryEntryFactory.create(type=TypeOfDictionaryEntry.WORD)
        mock_search_results = [
            self.get_dictionary_search_result(word),
            self.get_song_search_result(song),
        ]
        mock_data = {
            "Song": {str(song.id): song},
            "DictionaryEntry": {str(word.id): word},
        }

        viewset = BaseSearchViewSet()
        viewset.request = MagicMock()
        viewset.format_kwarg = MagicMock()
        viewset.serializer_classes = {
            "Song": MinimalSerializer,
            "DictionaryEntry": EagerSerializer,
        }

        actual = viewset.serialize_search_results(mock_search_results, mock_data)
        assert actual == [
            {"id": str(word.id), "title": word.title},
            {"id": str(song.id)},
        ]

    @pytest.mark.django_db
    def test_serialize_search_results_missing_data(self):
        song = factories.SongFactory.create()
        mock_search_results = [
            self.get_dictionary_search_result(),
            self.get_song_search_result(song),
        ]
        mock_data = {"Song": {str(song.id): song}}

        viewset = BaseSearchViewSet()
        viewset.request = MagicMock()
        viewset.format_kwarg = MagicMock()
        viewset.serializer_classes = {
            "Song": MinimalSerializer,
            "DictionaryEntry": EagerSerializer,
        }

        actual = viewset.serialize_search_results(mock_search_results, mock_data)
        assert actual == [{"id": str(song.id)}]
