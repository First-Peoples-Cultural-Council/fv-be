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
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
)


class TestWordOfTheDayEndpoint(BaseSiteContentApiTest):
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
    def test_wotd_unused_words_no_translations(self):
        # Ensure that words without translations are not selected as word of the day
        # even if they have not been used as word of the day before
        yesterday = self.today - timedelta(days=1)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC, translations=[]
        )
        dict_entry_3 = DictionaryEntryFactory.create(
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
        assert dictionary_entry["id"] == str(dict_entry_3.id)

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
            dictionary_entry=dict_entry_2, date=before_last_year_date, site=self.site
        )
        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]

        assert response_data_entry["date"] == str(self.today.date())
        assert dictionary_entry["id"] == str(dict_entry_2.id)

    @pytest.mark.django_db
    def test_words_not_used_in_last_year_no_translations(self):
        # Ensure that words without translations are not selected as word of the day
        # even if they are not used in the last year
        within_last_year_date = self.today - timedelta(weeks=30)
        before_last_year_date = self.today - timedelta(weeks=60)
        before_last_year_date_2 = self.today - timedelta(weeks=70)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        dict_entry_2 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC, translations=[]
        )
        dict_entry_3 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )

        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=within_last_year_date, site=self.site
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_2, date=before_last_year_date, site=self.site
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_3, date=before_last_year_date_2, site=self.site
        )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]

        assert response_data_entry["date"] == str(self.today.date())
        assert dictionary_entry["id"] == str(dict_entry_3.id)

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

    @pytest.mark.django_db
    def test_random_words_base_case_no_translations(self):
        # Ensure that words without translations are not selected as word of the day when selecting a word at random
        within_last_year_date_1 = self.today - timedelta(weeks=20)
        within_last_year_date_2 = self.today - timedelta(weeks=15)
        within_last_year_date_3 = self.today - timedelta(weeks=10)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        dict_entry_2 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC, translations=[]
        )
        dict_entry_3 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )

        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=within_last_year_date_1, site=self.site
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_2, date=within_last_year_date_2, site=self.site
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_3, date=within_last_year_date_3, site=self.site
        )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]

        assert response_data_entry["date"] == str(self.today.date())
        # entry 1 or 3 should be chosen
        assert dictionary_entry["id"] in [str(dict_entry_1.id), str(dict_entry_3.id)]

    @pytest.mark.django_db
    def test_permissions_applied_on_dictionary_entry(self):
        # Since the WOTD model has no permissions, we need to verify the dictionary entry
        # being returned satisfy the permissions
        dict_entry_1 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.TEAM
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=self.today, site=self.site
        )
        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        assert response.status_code == 200

        # Since we are using a non-member user, there should be no entry returned
        # even if the WOTD contains the above team visibility entry
        response_data = json.loads(response.content)
        assert len(response_data) == 0

    @pytest.mark.django_db
    def test_site_visibility_matching_entry_picked(self):
        # Verify that the words being chosen are having the same visibility as the site
        team_site, team_user = get_site_with_member(
            Visibility.TEAM, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=team_user)
        within_last_year_date = self.today - timedelta(weeks=20)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=team_site, visibility=Visibility.TEAM
        )
        dict_entry_2 = DictionaryEntryFactory.create(
            site=team_site, visibility=Visibility.TEAM
        )
        dict_entry_3 = DictionaryEntryFactory.create(
            site=team_site, visibility=Visibility.MEMBERS
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=within_last_year_date, site=team_site
        )

        # only dict_entry_2 should be chosen
        response = self.client.get(self.get_list_endpoint(site_slug=team_site.slug))
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]
        assert response_data_entry["date"] == str(self.today.date())
        assert dictionary_entry["id"] == str(dict_entry_2.id)
        assert dictionary_entry["id"] != str(dict_entry_3.id)

    @pytest.mark.django_db
    def test_site_visibility_matching_no_new_entry_picked(self):
        # Verify that the words being chosen are having the same visibility as the site
        team_site, team_user = get_site_with_member(
            Visibility.TEAM, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=team_user)
        within_last_year_date = self.today - timedelta(weeks=20)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=team_site, visibility=Visibility.TEAM
        )
        dict_entry_2 = DictionaryEntryFactory.create(
            site=team_site, visibility=Visibility.MEMBERS
        )
        dict_entry_3 = DictionaryEntryFactory.create(
            site=team_site, visibility=Visibility.MEMBERS
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=within_last_year_date, site=team_site
        )

        # only dict_entry_1 can be chosen
        response = self.client.get(self.get_list_endpoint(site_slug=team_site.slug))
        assert response.status_code == 200

        # since both the unassigned entries are members, they should not be chosen for a team site
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]
        dictionary_entry = response_data_entry["dictionaryEntry"]
        assert response_data_entry["date"] == str(self.today.date())
        assert dictionary_entry["id"] == str(dict_entry_1.id)
        assert dictionary_entry["id"] != str(dict_entry_2.id)
        assert dictionary_entry["id"] != str(dict_entry_3.id)
