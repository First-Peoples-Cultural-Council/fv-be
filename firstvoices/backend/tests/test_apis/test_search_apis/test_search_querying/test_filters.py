import pytest
from django.contrib.auth.models import AnonymousUser

import backend.tests.factories as factories
from backend.models.constants import AppRole, Role, Visibility
from backend.search.query_builder import get_search_query


@pytest.mark.django_db
class TestSearchFilters:
    def test_empty_site_id_allowed(self):
        search_query = get_search_query(q="something", sites="", user=AnonymousUser())
        search_query = search_query.to_dict()

        expected_site_filter = "'filter': [{'terms': {'site_id': ['']}}]"
        assert expected_site_filter not in str(search_query)

    def test_valid_dialect(self):
        valid_site = factories.SiteFactory.create()
        search_query = get_search_query(
            sites=[str(valid_site.id)], user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        expected_site_filter = (
            "'filter': [{'terms': {'site_id': ['" + str(valid_site.id) + "']}}]"
        )

        assert expected_site_filter in str(search_query)


@pytest.mark.django_db
class TestTypesFilter:
    @pytest.mark.parametrize(
        "type_to_exclude, expected_query",
        [
            (
                ["word"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'image', 'video', 'phrase']}}]}",
            ),
            (
                ["phrase"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'image', 'video', 'word']}}]}",
            ),
            (
                ["audio"],
                "'must_not': [{'terms': {'type': ['document', 'image', 'video', 'word', 'phrase']}}]}",
            ),
            (
                ["document"],
                "'must_not': [{'terms': {'type': ['audio', 'image', 'video', 'word', 'phrase']}}]}",
            ),
            (
                ["image"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'video', 'word', 'phrase']}}]}",
            ),
            (
                ["video"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'image', 'word', 'phrase']}}]}",
            ),
            (
                ["word", "audio"],
                "'must_not': [{'terms': {'type': ['document', 'image', 'video', 'phrase']}}]}",
            ),
            (
                ["word", "phrase"],
                "'must_not': [{'terms': {'type': ['audio', 'document', 'image', 'video']}}]}",
            ),
            (
                ["audio", "document", "image", "video"],
                "'must_not': [{'terms': {'type': ['word', 'phrase']}}]}",
            ),
            (
                ["audio", "phrase"],
                "'must_not': [{'terms': {'type': ['document', 'image', 'video', 'word']}}]}",
            ),
        ],
    )
    def test_exclusion_cases(self, type_to_exclude, expected_query):
        search_query = get_search_query(types=type_to_exclude, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_query in str(search_query)

    def test_all_types_supplied(self):
        search_query = get_search_query(
            types=["audio", "document", "image", "video", "word", "phrase"],
            user=AnonymousUser(),
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
    HAS_MEDIA = "has_media"
    HAS_MEDIA_LIST = ["has_audio", "has_document", "has_image", "has_video"]

    @pytest.mark.parametrize(HAS_MEDIA, HAS_MEDIA_LIST)
    def test_default(self, has_media):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"]["bool"] or has_media not in str(
            search_query["query"]["bool"]["filter"]
        )

    @pytest.mark.parametrize(HAS_MEDIA, HAS_MEDIA_LIST)
    def test_has_media_true(self, has_media):
        expected_true_filter = f"{{'term': {{'{has_media}': True}}}}"
        search_query = get_search_query(**{has_media: True}, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    @pytest.mark.parametrize(HAS_MEDIA, HAS_MEDIA_LIST)
    def test_has_media_false(self, has_media):
        expected_false_filter = f"{{'term': {{'{has_media}': False}}}}"
        search_query = get_search_query(**{has_media: False}, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    @pytest.mark.parametrize(HAS_MEDIA, HAS_MEDIA_LIST)
    def test_has_media_default(self, has_media):
        expected_true_filter = f"{{'term': {{'{has_media}': True}}}}"
        expected_false_filter = f"{{'term': {{'{has_media}': False}}}}"
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)


class TestHasSiteFeatureParams:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "filter" not in search_query["query"][
            "bool"
        ] or "site_features" not in str(search_query["query"]["bool"]["filter"])

    @pytest.mark.parametrize(
        "site_features",
        [
            [
                "SHARED_MEDIA",
            ],
            ["TEST_FEATURE_1", "TEST_FEATURE_2"],
            ["SHARED_MEDIA", "TEST_FEATURE_1", "TEST_FEATURE_2"],
        ],
    )
    def test_has_site_features(self, site_features):
        search_query = get_search_query(
            has_site_feature=site_features, user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        filtered_terms = search_query["query"]["bool"]["filter"][0]["terms"]
        assert "site_features" in filtered_terms
        assert len(filtered_terms["site_features"]) == len(site_features)

        for value in site_features:
            assert value in filtered_terms["site_features"]


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


class TestHasUnrecognizedCharsParam:
    def test_has_unrecognized_chars_true(self):
        expected_true_filter = "{'term': {'has_unrecognized_chars': True}}"
        search_query = get_search_query(
            has_unrecognized_chars=True, user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    def test_has_unrecognized_chars_false(self):
        expected_false_filter = "{'term': {'has_unrecognized_chars': False}}"
        search_query = get_search_query(
            has_unrecognized_chars=False, user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    def test_has_unrecognized_chars_default(self):
        expected_true_filter = "{'term': {'has_unrecognized_chars': True}}"
        expected_false_filter = "{'term': {'has_unrecognized_chars': False}}"

        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)
        assert "filter" not in search_query["query"][
            "bool"
        ] or "has_unrecognized_chars" not in str(
            search_query["query"]["bool"]["filter"]
        )


class TestHasCategoriesParam:
    def test_has_categories_true(self):
        expected_true_filter = "{'term': {'has_categories': True}}"
        search_query = get_search_query(has_categories=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    def test_has_categories_false(self):
        expected_false_filter = "{'term': {'has_categories': False}}"
        search_query = get_search_query(has_categories=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    def test_has_categories_default(self):
        expected_true_filter = "{'term': {'has_categories': True}}"
        expected_false_filter = "{'term': {'has_categories': False}}"

        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)
        assert "filter" not in search_query["query"][
            "bool"
        ] or "has_categories" not in str(search_query["query"]["bool"]["filter"])


class TestHasRelatedEntriesParam:
    def test_has_related_entries_true(self):
        expected_true_filter = "{'term': {'has_related_entries': True}}"
        search_query = get_search_query(has_related_entries=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter in str(search_query)

    def test_has_related_entries_false(self):
        expected_false_filter = "{'term': {'has_related_entries': False}}"
        search_query = get_search_query(has_related_entries=False, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_false_filter in str(search_query)

    def test_has_related_entries_default(self):
        expected_true_filter = "{'term': {'has_related_entries': True}}"
        expected_false_filter = "{'term': {'has_related_entries': False}}"

        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_true_filter not in str(search_query)
        assert expected_false_filter not in str(search_query)
        assert "filter" not in search_query["query"][
            "bool"
        ] or "has_related_entries" not in str(search_query["query"]["bool"]["filter"])


class TestRandomSortParams:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert (
            "must" not in search_query["query"]["bool"]
            or "function_score" not in search_query["query"]["bool"]["must"][0]
        )

    def test_random_sort_true(self):
        search_query = get_search_query(random_sort=True, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert "function_score" in search_query["query"]["bool"]["must"][0]
        search_query = search_query["query"]["bool"]["must"][0]["function_score"]
        assert "random_score" in search_query["functions"][0]
        assert "seed" in search_query["functions"][0]["random_score"]
        assert "field" in search_query["functions"][0]["random_score"]
        assert search_query["functions"][0]["random_score"]["field"] == "_seq_no"
        assert 1000 <= search_query["functions"][0]["random_score"]["seed"] <= 9999


class TestWordLengthParams:
    def test_default(self):
        search_query = get_search_query(user=AnonymousUser())
        search_query = search_query.to_dict()

        assert (
            "lte" not in search_query["query"]["bool"]
            and "gte" not in search_query["query"]["bool"]
        )

    def test_min_words(self):
        min_words = 2
        expected_min_words_filter = (
            "{'range': {'title.token_count': {'gte': " + str(min_words) + "}}}"
        )
        search_query = get_search_query(min_words=min_words, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_min_words_filter in str(search_query)

    def test_max_words(self):
        max_words = 5
        expected_max_words_filter = (
            "{'range': {'title.token_count': {'lte': " + str(max_words) + "}}}"
        )
        search_query = get_search_query(max_words=max_words, user=AnonymousUser())
        search_query = search_query.to_dict()

        assert expected_max_words_filter in str(search_query)

    def test_combined_filter(self):
        min_words = 2
        max_words = 5
        expected_min_words_filter = (
            "{'range': {'title.token_count': {'gte': " + str(min_words) + "}}}"
        )
        expected_max_words_filter = (
            "{'range': {'title.token_count': {'lte': " + str(max_words) + "}}}"
        )

        search_query = get_search_query(
            min_words=min_words, max_words=max_words, user=AnonymousUser()
        )
        search_query = search_query.to_dict()

        assert expected_min_words_filter in str(search_query)
        assert expected_max_words_filter in str(search_query)
