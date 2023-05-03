import json

import factory
import pytest
from django.utils.timezone import datetime, timedelta
from factory.django import DjangoModelFactory
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.models.dictionary import WordOfTheDay
from backend.tests.factories import (
    DictionaryEntryFactory,
    MembershipFactory,
    SiteFactory,
    get_non_member_user,
    get_site_with_member,
)
from backend.tests.test_apis.base_api_test import BaseSiteControlledContentApiTest


class WordOfTheDayFactory(DjangoModelFactory):
    dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
    date = datetime.today()

    class Meta:
        model = WordOfTheDay


class TestWordOfTheDayEndpoint(BaseSiteControlledContentApiTest):
    """
    Tests for the word-of-the-day API

    4. Test getting back words that are not used till now
    5. Test getting words not used within last year
    6. Test getting random words in the end.

    """

    API_LIST_VIEW = "api:word-of-the-day-list"

    def setup_method(self):
        self.public_client = APIClient()
        self.site, self.member_user = get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.public_client.force_authenticate(user=self.member_user)

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
        today = datetime.today()
        dict_entry = DictionaryEntryFactory(site=self.site)
        WordOfTheDayFactory(dictionary_entry=dict_entry, date=today, site=self.site)

        response = self.public_client.get(
            self.get_list_endpoint(site_slug=self.site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]

        assert response_data_entry["id"] == str(dict_entry.id)

    @pytest.mark.django_db
    def test_wotd_unused_words(self):
        # Creating 2 dictionary entries, one was used as a word of the day yesterday,
        # and there is one unused word which should be the word of the day for today.

        today = datetime.today()
        yesterday = today - timedelta(days=1)

        dict_entry_1 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        dict_entry_2 = DictionaryEntryFactory.create(
            site=self.site, visibility=Visibility.PUBLIC
        )
        WordOfTheDayFactory.create(
            dictionary_entry=dict_entry_1, date=yesterday, site=self.site
        )
        #
        # d = DictionaryEntry.objects.all()
        # x = WordOfTheDay.objects.all()

        response = self.public_client.get(
            self.get_list_endpoint(site_slug=self.site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        response_data_entry = response_data[0]

        assert response_data_entry["id"] == str(dict_entry_2.id)
