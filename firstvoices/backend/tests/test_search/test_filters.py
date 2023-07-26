import pytest

import backend.tests.factories as factories
from backend.models.constants import AppRole, Role
from backend.search.query_builder import get_search_query


@pytest.mark.django_db
class TestSearchFilters:
    def test_empty_site_id_allowed(self):
        search_query = get_search_query(q="something", site_id="")
        search_query = search_query.to_dict()

        expected_site_filter = "'filter': [{'term': {'site_id': ''}}]"
        assert expected_site_filter not in str(search_query)

    def test_valid_dialect(self):
        valid_site = factories.SiteFactory.create()
        search_query = get_search_query(site_id=str(valid_site.id))
        search_query = search_query.to_dict()

        expected_site_filter = (
            "'filter': [{'term': {'site_id': '" + str(valid_site.id) + "'}}]"
        )

        assert expected_site_filter in str(search_query)


@pytest.mark.django_db
class TestTypesFilter:
    expected_phrases_filter = "'must_not': [{'match': {'type': 'phrase'}}]}"
    expected_word_filter = "'must_not': [{'match': {'type': 'word'}}]}"

    def test_words(self):
        search_query = get_search_query(types=["word"])
        search_query = search_query.to_dict()

        assert self.expected_phrases_filter in str(search_query)
        assert self.expected_word_filter not in str(search_query)

    def test_phrases(self):
        search_query = get_search_query(types=["phrase"])
        search_query = search_query.to_dict()

        assert self.expected_phrases_filter not in str(search_query)
        assert self.expected_word_filter in str(search_query)

    @pytest.mark.parametrize("types", [["phrase", "word"], ["word", "phrase"]])
    def test_words_and_phrases(self, types):
        search_query = get_search_query(types=types)
        search_query = search_query.to_dict()

        assert self.expected_phrases_filter not in str(search_query)
        assert self.expected_word_filter not in str(search_query)


@pytest.mark.django_db
class TestKids:
    expected_kids_filter = "{'term': {'exclude_from_kids': False}}"

    def test_kids_true(self):
        search_query = get_search_query(kids=True)
        search_query = search_query.to_dict()

        assert self.expected_kids_filter in str(search_query)

    def test_kids_false(self):
        search_query = get_search_query(kids=False)
        search_query = search_query.to_dict()

        assert self.expected_kids_filter not in search_query

    def test_default(self):
        search_query = get_search_query()
        search_query = search_query.to_dict()

        assert self.expected_kids_filter not in search_query


@pytest.mark.django_db
class TestGames:
    expected_games_filter = "{'term': {'exclude_from_games': False}}"

    def test_games_true(self):
        search_query = get_search_query(games=True)
        search_query = search_query.to_dict()

        assert self.expected_games_filter in str(search_query)

    def test_games_false(self):
        search_query = get_search_query(games=False)
        search_query = search_query.to_dict()

        assert self.expected_games_filter not in search_query

    def test_default(self):
        search_query = get_search_query()
        search_query = search_query.to_dict()

        assert self.expected_games_filter not in search_query


class TestSearchPermissions:
    public_permissions_filter = (
        "'must': [{'term': {'site_visibility': Visibility.PUBLIC}}, {'term': {'visibility': "
        "Visibility.PUBLIC}}]"
    )
    member_permissions_snippet = (
        "{'range': {'visibility': {'gte': Visibility.MEMBERS}}}]"
    )
    team_permissions_snippet = "{'range': {'visibility': {'gte': Visibility.TEAM}}}]"

    @pytest.mark.django_db
    def test_no_user(self):
        search_query = get_search_query()
        search_query = search_query.to_dict()

        assert self.public_permissions_filter in str(search_query)
        assert self.member_permissions_snippet not in str(search_query)
        assert self.team_permissions_snippet not in str(search_query)

    @pytest.mark.django_db
    def test_no_permissions(self):
        user = factories.get_non_member_user()
        search_query = get_search_query(user=user)
        search_query = search_query.to_dict()

        assert self.public_permissions_filter in str(search_query)
        assert self.member_permissions_snippet not in str(search_query)
        assert self.team_permissions_snippet not in str(search_query)

    @pytest.mark.django_db
    def test_member_permissions(self):
        user = factories.get_non_member_user()
        site = factories.SiteFactory.create()
        factories.MembershipFactory.create(user=user, site=site, role=Role.MEMBER)

        member_permissions_filter = (
            "'must': [{'term': {'site_id': UUID('"
            + str(site.id)
            + "')}}, {'range': {'visibility': {'gte': Visibility.MEMBERS}}}]"
        )

        search_query = get_search_query(user=user)
        search_query = search_query.to_dict()

        assert self.public_permissions_filter in str(search_query)
        assert member_permissions_filter in str(search_query)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.LANGUAGE_ADMIN, Role.EDITOR, Role.ASSISTANT])
    def test_team_permissions(self, role):
        user = factories.get_non_member_user()
        site = factories.SiteFactory.create()
        factories.MembershipFactory.create(user=user, site=site, role=role)

        assistant_permissions_filter = (
            "'must': [{'term': {'site_id': UUID('"
            + str(site.id)
            + "')}}, {'range': {'visibility': {'gte': Visibility.TEAM}}}]"
        )

        search_query = get_search_query(user=user)
        search_query = search_query.to_dict()

        assert self.public_permissions_filter in str(search_query)
        assert assistant_permissions_filter in str(search_query)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [AppRole.SUPERADMIN, AppRole.STAFF])
    def test_staff_permissions(self, role):
        user = factories.get_app_admin(role=role)
        factories.SiteFactory.create()

        search_query = get_search_query(user=user)
        search_query = search_query.to_dict()

        assert self.public_permissions_filter not in str(search_query)
