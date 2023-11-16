import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
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
        return {
            "aggregate": {
                "words": {
                    "total": 0,
                    "availableInChildrensArchive": 0,
                    "public": 0,
                },
                "phrases": {
                    "total": 0,
                    "availableInChildrensArchive": 0,
                    "public": 0,
                },
                "songs": {
                    "total": 0,
                    "availableInChildrensArchive": 0,
                    "public": 0,
                },
                "stories": {
                    "total": 0,
                    "availableInChildrensArchive": 0,
                    "public": 0,
                },
                "images": {
                    "total": 0,
                    "availableInChildrensArchive": 0,
                },
                "audio": {
                    "total": 0,
                    "availableInChildrensArchive": 0,
                },
                "video": {
                    "total": 0,
                    "availableInChildrensArchive": 0,
                },
            },
            "temporal": {
                "words": {
                    "lastYear": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last6Months": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last3Months": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "lastMonth": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "lastWeek": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last3Days": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "today": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                },
                "phrases": {
                    "lastYear": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last6Months": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last3Months": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "lastMonth": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "lastWeek": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last3Days": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "today": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                },
                "songs": {
                    "lastYear": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last6Months": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last3Months": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "lastMonth": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "lastWeek": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last3Days": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "today": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                },
                "stories": {
                    "lastYear": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last6Months": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last3Months": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "lastMonth": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "lastWeek": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "last3Days": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                    "today": {
                        "created": 0,
                        "lastModified": 0,
                        "public": 0,
                        "members": 0,
                        "team": 0,
                    },
                },
                "images": {
                    "lastYear": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last6Months": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last3Months": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "lastMonth": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "lastWeek": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last3Days": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "today": {
                        "created": 0,
                        "lastModified": 0,
                    },
                },
                "audio": {
                    "lastYear": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last6Months": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last3Months": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "lastMonth": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "lastWeek": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last3Days": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "today": {
                        "created": 0,
                        "lastModified": 0,
                    },
                },
                "video": {
                    "lastYear": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last6Months": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last3Months": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "lastMonth": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "lastWeek": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "last3Days": {
                        "created": 0,
                        "lastModified": 0,
                    },
                    "today": {
                        "created": 0,
                        "lastModified": 0,
                    },
                },
            },
        }

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
        pass

    # TODO: Add tests for the following:
    # - Test each aggregate by model
    # - Test each temporal by model and time range
