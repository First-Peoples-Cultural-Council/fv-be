import pytest
from django.contrib.auth.models import AnonymousUser

import backend.tests.factories as factories
from backend.models.constants import AppRole, Role, Visibility
from backend.search.query_builder import get_search_query


@pytest.mark.django_db
class TestSearchFilters:
    def test_empty_site_id_allowed(self):
        search_query = get_search_query(q="something", site_id="", user=AnonymousUser())
        search_query = search_query.to_dict()

        expected_site_filter = "'filter': [{'term': {'site_id': ''}}]"
        assert expected_site_filter not in str(search_query)

    def test_valid_dialect(self):
        valid_site = factories.SiteFactory.create()
        search_query = get_search_query(
            site_id=str(valid_site.id), user=AnonymousUser()
        )
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
        search_query = get_search_query(types=type_to_exclude, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_query in str(search_query)

    def test_all_types_supplied(self):
        search_query = get_search_query(
            types=["audio", "image", "video", "word", "phrase"], user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        # Checking there must not be a filter present for types in the query
        assert "'must_not': [{'terms': {'type':" not in str(search_query)


@pytest.mark.django_db
class TestKids:
    # The following boolean flags in the query are opposite of input parameter as
    # the model attribute represent an exclusion criteria
    expected_kids_true_filter = "{'term': {'exclude_from_kids': False}}"
    expected_kids_false_filter = "{'term': {'exclude_from_kids': True}}"

    def test_kids_true(self):
        search_query = get_search_query(kids=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_kids_true_filter in str(search_query)

    def test_kids_false(self):
        search_query = get_search_query(kids=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_kids_false_filter in str(search_query)

    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_kids_true_filter not in str(search_query)
        assert self.expected_kids_false_filter not in str(search_query)


@pytest.mark.django_db
class TestGames:
    # The following boolean flags in the query are opposite of input parameter as
    # the model attribute represent an exclusion criteria
    expected_games_true_filter = "{'term': {'exclude_from_games': False}}"
    expected_games_false_filter = "{'term': {'exclude_from_games': True}}"

    def test_games_true(self):
        search_query = get_search_query(games=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_games_true_filter in str(search_query)

    def test_games_false(self):
        search_query = get_search_query(games=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_games_false_filter in str(search_query)

    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert self.expected_games_true_filter not in str(search_query)
        assert self.expected_games_false_filter not in str(search_query)


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
        search_query = get_search_query(user=AnonymousUser())
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
        search_query = get_search_query(user=AnonymousUser())
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
        search_query = get_search_query(visibility=visibility, user=AnonymousUser())
        search_query = search_query.to_dict()

        filtered_terms = search_query["query"]["bool"]["filter"][0]["terms"]
        assert "visibility" in filtered_terms
        assert len(filtered_terms["visibility"]) == len(visibility)

        for value in visibility:
            assert value in filtered_terms["visibility"]


class TestHasMediaParams:
    @pytest.mark.parametrize("has_media", ["has_video", "has_audio", "has_image"])
    def test_default(self, has_media):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"]["bool"] or has_media not in str(
            search_query["query"]["bool"]["filter"]
        )

    @pytest.mark.parametrize("has_media", ["has_video", "has_audio", "has_image"])
    def test_has_media_true(self, has_media):
        expected_true_filter = f"{{'term': {{'{has_media}': True}}}}"
        search_query = get_search_query(**{has_media: True}, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    @pytest.mark.parametrize("has_media", ["has_video", "has_audio", "has_image"])
    def test_has_media_false(self, has_media):
        expected_false_filter = f"{{'term': {{'{has_media}': False}}}}"
        search_query = get_search_query(**{has_media: False}, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    @pytest.mark.parametrize("has_media", ["has_video", "has_audio", "has_image"])
    def test_has_media_default(self, has_media):
        expected_true_filter = f"{{'term': {{'{has_media}': True}}}}"
        expected_false_filter = f"{{'term': {{'{has_media}': False}}}}"
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)


class TestHasTranslationParams:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"][
            "bool"
        ] or "has_translation" not in str(search_query["query"]["bool"]["filter"])

    def test_has_translation_true(self):
        expected_true_filter = "{'term': {'has_translation': True}}"
        search_query = get_search_query(has_translation=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    def test_has_translation_false(self):
        expected_false_filter = "{'term': {'has_translation': False}}"
        search_query = get_search_query(has_translation=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    def test_has_translation_default(self):
        expected_true_filter = "{'term': {'has_translation': True}}"
        expected_false_filter = "{'term': {'has_translation': False}}"
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)
