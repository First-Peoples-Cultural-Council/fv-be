import json

import pytest
from django.utils.timezone import datetime, timedelta
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.tests.factories import (
    DictionaryEntryFactory,
    MembershipFactory,
    SiteFactory,
    WordOfTheDayFactory,
    get_non_member_user,
    get_site_with_member,
)
from backend.tests.test_apis.base_api_test import BaseSiteControlledContentApiTest


class TestWordOfTheDayEndpoint(BaseSiteControlledContentApiTest):
    """
    Tests for the word-of-the-day API
    """

    API_LIST_VIEW = "api:word-of-the-day-list"

    def setup_method(self):
        self.client = APIClient()
        self.site, self.member_user = get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.non_member_user = get_non_member_user()
        self.client.force_authenticate(user=self.non_member_user)
        self.today = datetime.today()

    @pytest.mark.django_db
    def test_detail_404_unknown_key(self):
        # Ignoring test since there is no detail view for this endpoint
        pass

    @pytest.mark.django_db
    def test_list_empty(self):
        # Overriding since there is no pagination class for this view
        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 0

    @pytest.mark.django_db
    def test_list_team_access(self):
        # Overriding since there is no pagination class for this view
        site = SiteFactory.create(visibility=Visibility.TEAM)
        user = get_non_member_user()
        MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == []

    @pytest.mark.django_db
    def test_wotd_today_date(self):
        dict_entry = DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC
        )
        WordOfTheDayFactory(
            dictionary_entry=dict_entry, date=self.today, site=self.site
        )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]

        assert response_data_entry["date"] == str(self.today.date())
        assert dictionary_entry["id"] == str(dict_entry.id)

    @pytest.mark.django_db
    def test_wotd_unused_words(self):
        # Creating 2 dictionary entries, one was used as a word of the day yesterday,
        # and there is one unused word which should be the word of the day for today.
        yesterday = self.today - timedelta(days=1)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        dict_entry_2 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=yesterday, site=self.site
        )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]

        assert response_data_entry["date"] == str(self.today.date())
        assert dictionary_entry["id"] == str(dict_entry_2.id)

    @pytest.mark.django_db
    def test_words_not_used_in_last_year(self):
        # Creating 2 dictionary entries, one of which are used in the last year
        # and one which is not used within last year

        within_last_year_date = self.today - timedelta(weeks=30)
        before_last_year_date = self.today - timedelta(weeks=60)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        dict_entry_2 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=within_last_year_date, site=self.site
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=before_last_year_date, site=self.site
        )
        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]

        assert response_data_entry["date"] == str(self.today.date())
        assert dictionary_entry["id"] == str(dict_entry_2.id)

    @pytest.mark.django_db
    def test_random_words_base_case(self):
        # If no words pass any of the above cases, a random word will be chosen and returned

        within_last_year_date_1 = self.today - timedelta(weeks=20)
        within_last_year_date_2 = self.today - timedelta(weeks=15)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        dict_entry_2 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=within_last_year_date_1, site=self.site
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_2, date=within_last_year_date_2, site=self.site
        )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]

        assert response_data_entry["date"] == str(self.today.date())

        # any 1 of the 2 entries
        assert dictionary_entry["id"] in [str(dict_entry_1.id), str(dict_entry_2.id)]
