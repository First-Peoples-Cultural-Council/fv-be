import pytest

import backend.tests.factories as factories
from backend.models.constants import AppRole, Role, Visibility
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
    @pytest.mark.parametrize(
        "type_to_exclude, expected_query",
        [
            (
                ["word"],
                "'must_not': [{'terms': {'type': ['audio', 'image', 'video', 'phrase']}}]}",
            ),
            (
                ["phrase"],
                "'must_not': [{'terms': {'type': ['audio', 'image', 'video', 'word']}}]}",
            ),
            (
                ["image"],
                "'must_not': [{'terms': {'type': ['audio', 'video', 'word', 'phrase']}}]}",
            ),
            (
                ["audio"],
                "'must_not': [{'terms': {'type': ['image', 'video', 'word', 'phrase']}}]}",
            ),
            (
                ["video"],
                "'must_not': [{'terms': {'type': ['audio', 'image', 'word', 'phrase']}}]}",
            ),
            (
                ["word", "audio"],
                "'must_not': [{'terms': {'type': ['image', 'video', 'phrase']}}]}",
            ),
            (
                ["word", "phrase"],
                "'must_not': [{'terms': {'type': ['audio', 'image', 'video']}}]}",
            ),
            (
                ["audio", "image", "video"],
                "'must_not': [{'terms': {'type': ['word', 'phrase']}}]}",
            ),
            (
                ["audio", "phrase"],
                "'must_not': [{'terms': {'type': ['image', 'video', 'word']}}]}",
            ),
        ],
    )
    def test_exclusion_cases(self, type_to_exclude, expected_query):
        search_query = get_search_query(types=type_to_exclude)
        search_query = search_query.to_dict()

        assert expected_query in str(search_query)

    def test_all_types_supplied(self):
        search_query = get_search_query(
            types=["audio", "image", "video", "word", "phrase"]
        )
        search_query = search_query.to_dict()

        # Checking there must not be a filter present for types in the query
        assert "'must_not': [{'terms': {'type':" not in str(search_query)


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


class TestVisibilityParam:
    def test_default(self):
        search_query = get_search_query()
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"]["bool"] or "visibility" not in str(
            search_query["query"]["bool"]["filter"]
        )

    @pytest.mark.parametrize(
        "visibility",
        [
            [Visibility.PUBLIC],
            [Visibility.MEMBERS],
            [Visibility.TEAM],
            [Visibility.PUBLIC, Visibility.MEMBERS],
            [Visibility.PUBLIC, Visibility.TEAM],
            [Visibility.MEMBERS, Visibility.TEAM],
            [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
        ],
    )
    def test_team(self, visibility):
        search_query = get_search_query(visibility=visibility)
        search_query = search_query.to_dict()

        filtered_terms = search_query["query"]["bool"]["filter"][0]["terms"]
        assert "visibility" in filtered_terms
        assert len(filtered_terms["visibility"]) == len(visibility)

        for value in visibility:
            assert value in filtered_terms["visibility"]


class TestHasMediaParams:
    @staticmethod
    def snake_case_to_camel_case(snake_str):
        temp = snake_str.split("_")
        result = temp[0] + "".join(ele.title() for ele in temp[1:])
        return result

    @pytest.mark.parametrize("has_media", ["has_video", "has_audio", "has_image"])
    def test_default(self, has_media):
        search_query = get_search_query()
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"][
            "bool"
        ] or self.snake_case_to_camel_case(has_media) not in str(
            search_query["query"]["bool"]["filter"]
        )

    @pytest.mark.parametrize("has_media", ["has_video", "has_audio", "has_image"])
    def test_has_media_true(self, has_media):
        expected_true_filter = (
            f"{{'term': {{'{self.snake_case_to_camel_case(has_media)}': True}}}}"
        )
        search_query = get_search_query(**{has_media: True})
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    @pytest.mark.parametrize("has_media", ["has_video", "has_audio", "has_image"])
    def test_has_media_false(self, has_media):
        expected_true_filter = (
            f"{{'term': {{'{self.snake_case_to_camel_case(has_media)}': False}}}}"
        )
        search_query = get_search_query(**{has_media: False})
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
