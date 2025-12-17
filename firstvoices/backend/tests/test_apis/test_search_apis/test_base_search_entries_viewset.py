from unittest.mock import MagicMock

import pytest

from backend.models.constants import AppRole, Role
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.tests.test_apis.test_search_apis.base_search_test import SearchMocksMixin
from backend.views.base_search_entries_views import BaseSearchEntriesViewSet


class TestBaseSearchViewSet(SearchMocksMixin):

    def set_up_mock_search_result(self, site=None):
        if site is None:
            site = factories.SiteFactory.create()

        image = factories.ImageFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)
        document = factories.DocumentFactory.create(site=site)
        song = factories.SongFactory.create(site=site)
        story = factories.StoryFactory.create(site=site)
        word = factories.DictionaryEntryFactory.create(
            type=TypeOfDictionaryEntry.WORD, site=site
        )

        mock_search_results = [
            self.get_image_search_result(image),
            self.get_audio_search_result(audio),
            self.get_video_search_result(video),
            self.get_document_search_result(document),
            self.get_song_search_result(song),
            self.get_story_search_result(story),
            self.get_dictionary_search_result(word),
        ]

        return (
            mock_search_results,
            image,
            audio,
            video,
            document,
            song,
            story,
            word,
        )

    def assert_author_fields_present(self, viewset, site=None):
        mock_search_results, image, audio, video, document, song, story, word = (
            self.set_up_mock_search_result(site=site)
        )

        hydrated_data = viewset.hydrate(mock_search_results)
        serialized_data = viewset.serialize_search_results(
            mock_search_results, hydrated_data
        )

        for serialized_entry, original_entry in zip(
            serialized_data, [image, audio, video, document, song, story, word]
        ):
            assert str(serialized_entry["entry"]["created_by"]) == str(
                original_entry.created_by
            )
            assert str(serialized_entry["entry"]["last_modified_by"]) == str(
                original_entry.last_modified_by
            )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "app_role",
        [
            AppRole.STAFF,
            AppRole.SUPERADMIN,
        ],
    )
    def test_serialized_entries_have_author_fields_staff(self, app_role):
        user = factories.UserFactory.create()
        factories.AppMembershipFactory.create(user=user, role=app_role)

        viewset = BaseSearchEntriesViewSet()
        viewset.request = self.create_mock_request(user=user, query_dict={})
        viewset.format_kwarg = MagicMock()

        self.assert_author_fields_present(viewset)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_serialized_entries_have_author_fields_authorized(self, role):
        user = factories.UserFactory.create()
        site = factories.SiteFactory.create()
        factories.MembershipFactory.create(user=user, role=role, site=site)

        viewset = BaseSearchEntriesViewSet()
        viewset.request = self.create_mock_request(user=user, query_dict={})
        viewset.format_kwarg = MagicMock()

        self.assert_author_fields_present(viewset, site=site)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_serialized_entries_hide_author_fields_wrong_site(self, role):
        user = factories.UserFactory.create()
        site = factories.SiteFactory.create()
        factories.MembershipFactory.create(user=user, role=role, site=site)

        (
            mock_search_results,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = self.set_up_mock_search_result()

        viewset = BaseSearchEntriesViewSet()
        viewset.request = self.create_mock_request(user=user, query_dict={})
        viewset.format_kwarg = MagicMock()

        hydrated_data = viewset.hydrate(mock_search_results)
        serialized_data = viewset.serialize_search_results(
            mock_search_results, hydrated_data
        )

        for serialized_entry in serialized_data:
            assert "created_by" not in serialized_entry["entry"]
            assert "last_modified_by" not in serialized_entry["entry"]

    @pytest.mark.django_db
    def test_serialized_entries_hide_author_fields_members(self):
        user = factories.UserFactory.create()
        site = factories.SiteFactory.create()
        factories.MembershipFactory.create(user=user, role=Role.MEMBER, site=site)

        (
            mock_search_results,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = self.set_up_mock_search_result(site=site)

        viewset = BaseSearchEntriesViewSet()
        viewset.request = self.create_mock_request(user=user, query_dict={})
        viewset.format_kwarg = MagicMock()

        hydrated_data = viewset.hydrate(mock_search_results)
        serialized_data = viewset.serialize_search_results(
            mock_search_results, hydrated_data
        )

        for serialized_entry in serialized_data:
            assert "created_by" not in serialized_entry["entry"]
            assert "last_modified_by" not in serialized_entry["entry"]

    @pytest.mark.django_db
    def test_serialized_entries_hide_author_fields_anonymous(self):
        user = factories.get_anonymous_user()
        (
            mock_search_results,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = self.set_up_mock_search_result()

        viewset = BaseSearchEntriesViewSet()
        viewset.request = self.create_mock_request(user=user, query_dict={})
        viewset.format_kwarg = MagicMock()

        hydrated_data = viewset.hydrate(mock_search_results)
        serialized_data = viewset.serialize_search_results(
            mock_search_results, hydrated_data
        )

        for serialized_entry in serialized_data:
            assert "created_by" not in serialized_entry["entry"]
            assert "last_modified_by" not in serialized_entry["entry"]
