import json
from datetime import date

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentListEndpointMixin,
)
from backend.views.exceptions import (
    MatomoConfigurationError,
    MatomoError,
    MatomoTimeoutError,
)


@pytest.mark.django_db
class TestAnalyticsEndpoint(SiteContentListEndpointMixin, BaseSiteContentApiTest):
    API_LIST_VIEW = "api:analytics-list"

    @pytest.fixture(autouse=True)
    def mock_matomo(self, mocker):
        self.get_visitors = mocker.patch(
            "backend.views.analytics_views.get_monthly_visitors",
            return_value={"total_visits": 590, "unique_visitors": 364},
        )

    @pytest.mark.parametrize(
        "query_params",
        [
            {"date": "2024-02-15"},
            {"date": "2024-02-15", "period": "month"},
        ],
    )
    def test_monthly_analytics(self, query_params):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.LANGUAGE_ADMIN
        )

        response = self.client.get(self.get_list_endpoint(site.slug), query_params)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {
            "scope": {"type": "site", "slug": site.slug},
            "period": {
                "type": "month",
                "startDate": "2024-02-01",
                "endDate": "2024-02-29",
                "timezone": "America/Vancouver",
            },
            "metrics": {"totalVisits": 590, "uniqueVisitors": 364},
        }
        self.get_visitors.assert_called_once_with(site.slug, date(2024, 2, 1))

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    def test_insufficient_site_role(self, role):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=role
        )

        response = self.client.get(
            self.get_list_endpoint(site.slug), {"date": "2024-02-15"}
        )

        assert response.status_code == 403
        self.get_visitors.assert_not_called()

    def test_anonymous_access_denied(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_list_endpoint(site.slug), {"date": "2024-02-15"}
        )

        assert response.status_code == 401
        self.get_visitors.assert_not_called()

    @pytest.mark.parametrize("app_role", [AppRole.STAFF, AppRole.SUPERADMIN])
    def test_app_admin_access(self, app_role):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.TEAM, role=app_role
        )

        response = self.client.get(
            self.get_list_endpoint(site.slug), {"date": "2024-02-15"}
        )

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "query_params, error_field",
        [
            ({}, "date"),
            ({"date": "not-a-date"}, "date"),
            ({"date": "2024-02-15", "period": "week"}, "period"),
            ({"startDate": "2026-10-01", "endDate": "2026-10-31"}, "date"),
        ],
    )
    def test_invalid_query_parameters(self, query_params, error_field):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.LANGUAGE_ADMIN
        )

        response = self.client.get(self.get_list_endpoint(site.slug), query_params)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert error_field in response_data
        self.get_visitors.assert_not_called()

    def test_unknown_query_parameters_ignored(self):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.LANGUAGE_ADMIN
        )

        response = self.client.get(
            self.get_list_endpoint(site.slug),
            {"date": "2024-02-15", "extra": "ignored"},
        )

        assert response.status_code == 200
        self.get_visitors.assert_called_once_with(site.slug, date(2024, 2, 1))

    @pytest.mark.parametrize(
        "report_date, start_date, end_date",
        [
            ("2025-02-15", "2025-02-01", "2025-02-28"),
            ("2025-12-31", "2025-12-01", "2025-12-31"),
            ("2026-04-15", "2026-04-01", "2026-04-30"),
        ],
    )
    def test_month_boundaries(self, report_date, start_date, end_date):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.LANGUAGE_ADMIN
        )

        response = self.client.get(
            self.get_list_endpoint(site.slug), {"date": report_date}
        )

        assert response.status_code == 200
        period = json.loads(response.content)["period"]

        assert period["startDate"] == start_date
        assert period["endDate"] == end_date
        self.get_visitors.assert_called_once_with(
            site.slug, date.fromisoformat(start_date)
        )

    def test_future_date_rejected(self, mocker):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.LANGUAGE_ADMIN
        )
        mocker.patch(
            "backend.serializers.analytics_serializers.timezone.localdate",
            return_value=date(2026, 11, 13),
        )

        response = self.client.get(
            self.get_list_endpoint(site.slug), {"date": "2026-11-14"}
        )

        assert response.status_code == 400
        assert "date" in json.loads(response.content)
        self.get_visitors.assert_not_called()

    @pytest.mark.parametrize(
        "exception, expected_status",
        [
            (MatomoError, 502),
            (MatomoConfigurationError, 503),
            (MatomoTimeoutError, 504),
        ],
    )
    def test_upstream_error_response(self, exception, expected_status):
        site, _ = factories.get_site_with_authenticated_member(
            self.client, visibility=Visibility.PUBLIC, role=Role.LANGUAGE_ADMIN
        )
        self.get_visitors.side_effect = exception

        response = self.client.get(
            self.get_list_endpoint(site.slug), {"date": "2024-02-15"}
        )

        assert response.status_code == expected_status
        assert json.loads(response.content) == {"detail": exception.default_detail}
