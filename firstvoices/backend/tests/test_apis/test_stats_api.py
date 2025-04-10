import json

import pytest

from backend.models.constants import Role, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.tests.test_apis.base.base_api_test import (
    BaseSiteContentApiTest,
    SiteContentListApiTestMixin,
)


class TestStatsEndpoint(SiteContentListApiTestMixin, BaseSiteContentApiTest):
    """
    End-to-end tests that the stats endpoint has the expected behaviour.
    """

    API_LIST_VIEW = "api:stats-list"

    @staticmethod
    def get_empty_stats_page():
        data_models = ["words", "phrases", "songs", "stories"]
        media_models = ["images", "audio", "video"]
        time_periods = [
            "lastYear",
            "last6Months",
            "last3Months",
            "lastMonth",
            "lastWeek",
            "last3Days",
            "today",
        ]

        aggregate_data = {}
        for data_model in data_models:
            aggregate_data[data_model] = {
                "total": 0,
                "availableInChildrensArchive": 0,
                "public": 0,
            }

        for media_model in media_models:
            aggregate_data[media_model] = {
                "total": 0,
                "availableInChildrensArchive": 0,
            }

        temporal_data = {}
        for data_model in data_models:
            temporal_data[data_model] = {}
            for time_period in time_periods:
                temporal_data[data_model][time_period] = {
                    "created": 0,
                    "lastModified": 0,
                    "public": 0,
                    "members": 0,
                    "team": 0,
                }

        for media_model in media_models:
            temporal_data[media_model] = {}
            for time_period in time_periods:
                temporal_data[media_model][time_period] = {
                    "created": 0,
                    "lastModified": 0,
                }

        return {
            "aggregate": aggregate_data,
            "temporal": temporal_data,
        }

    @staticmethod
    def assert_temporal_stats(response_data, model, time_deltas):
        for time in time_deltas:
            assert response_data["temporal"][model][time]["created"] == 3
            assert response_data["temporal"][model][time]["lastModified"] == 3
            assert response_data["temporal"][model][time]["public"] == 1
            assert response_data["temporal"][model][time]["members"] == 1
            assert response_data["temporal"][model][time]["team"] == 1

    @pytest.fixture
    def time_deltas(self):
        return [
            "lastYear",
            "last6Months",
            "last3Months",
            "lastMonth",
            "lastWeek",
            "last3Days",
            "today",
        ]

    @pytest.mark.django_db
    def test_list_empty(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == self.get_empty_stats_page()

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == self.get_empty_stats_page()

    @pytest.mark.django_db
    def test_list_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == self.get_empty_stats_page()

    @pytest.mark.skip(reason="Stats API does not create an instance")
    def test_list_minimal(self):
        # Stats API does not create a model instance
        pass

    @pytest.mark.django_db
    @pytest.mark.parametrize("entry_type", TypeOfDictionaryEntry)
    def test_aggregate_stats_dictionary(self, entry_type):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.DictionaryEntryFactory.create(
            type=entry_type, site=site, visibility=Visibility.PUBLIC
        )
        factories.DictionaryEntryFactory.create(
            type=entry_type, site=site, visibility=Visibility.TEAM
        )
        factories.DictionaryEntryFactory.create(
            type=entry_type,
            site=site,
            visibility=Visibility.MEMBERS,
            exclude_from_kids=True,
        )

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        key = f"{entry_type}s"
        assert response_data["aggregate"][key]["total"] == 3
        assert response_data["aggregate"][key]["availableInChildrensArchive"] == 2
        assert response_data["aggregate"][key]["public"] == 1

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "model_factory, key",
        [(factories.SongFactory, "songs"), (factories.StoryFactory, "stories")],
    )
    def test_aggregate_stats_songs_stories(self, model_factory, key):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        model_factory.create(site=site, visibility=Visibility.PUBLIC)
        model_factory.create(site=site, visibility=Visibility.TEAM)
        model_factory.create(
            site=site, visibility=Visibility.MEMBERS, exclude_from_kids=True
        )

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["aggregate"][key]["total"] == 3
        assert response_data["aggregate"][key]["availableInChildrensArchive"] == 2
        assert response_data["aggregate"][key]["public"] == 1

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "model_factory, key",
        [
            (factories.ImageFactory, "images"),
            (factories.AudioFactory, "audio"),
            (factories.VideoFactory, "video"),
        ],
    )
    def test_aggregate_stats_media(self, model_factory, key):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        model_factory.create(site=site)
        model_factory.create(site=site, exclude_from_kids=True)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["aggregate"][key]["total"] == 2
        assert response_data["aggregate"][key]["availableInChildrensArchive"] == 1

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "entry_type, key",
        [
            (TypeOfDictionaryEntry.WORD, "words"),
            (TypeOfDictionaryEntry.PHRASE, "phrases"),
        ],
    )
    def test_temporal_stats_dictionary(self, entry_type, key, time_deltas):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.DictionaryEntryFactory.create(
            type=entry_type, site=site, visibility=Visibility.PUBLIC
        )
        factories.DictionaryEntryFactory.create(
            type=entry_type, site=site, visibility=Visibility.TEAM
        )
        factories.DictionaryEntryFactory.create(
            type=entry_type, site=site, visibility=Visibility.MEMBERS
        )

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        self.assert_temporal_stats(response_data, key, time_deltas)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "model_factory, key",
        [(factories.SongFactory, "songs"), (factories.StoryFactory, "stories")],
    )
    def test_temporal_stats_songs_stories(self, model_factory, key, time_deltas):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        model_factory.create(site=site, visibility=Visibility.PUBLIC)
        model_factory.create(site=site, visibility=Visibility.TEAM)
        model_factory.create(site=site, visibility=Visibility.MEMBERS)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        self.assert_temporal_stats(response_data, key, time_deltas)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "model_factory, key",
        [
            (factories.ImageFactory, "images"),
            (factories.AudioFactory, "audio"),
            (factories.VideoFactory, "video"),
        ],
    )
    def test_temporal_stats_media(self, model_factory, key, time_deltas):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        model_factory.create(site=site)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        for time in time_deltas:
            assert response_data["temporal"][key][time]["created"] == 1
            assert response_data["temporal"][key][time]["lastModified"] == 1
