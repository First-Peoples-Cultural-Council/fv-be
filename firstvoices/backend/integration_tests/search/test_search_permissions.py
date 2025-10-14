import pytest
from django.core.management import call_command
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

import backend.tests.factories as factories
from backend.models import (
    AppJson,
    Audio,
    DictionaryEntry,
    Document,
    Image,
    Site,
    Song,
    Story,
    Video,
)
from backend.models.constants import AppRole, Role, Visibility
from backend.models.sites import SiteFeature


@pytest.mark.django_db(transaction=True)
class TestSearchPermissions:

    def clear_entries(self):
        DictionaryEntry.objects.filter(site=self.site).delete()
        DictionaryEntry.objects.filter(site=self.shared_media_site).delete()
        Song.objects.filter(site=self.site).delete()
        Song.objects.filter(site=self.shared_media_site).delete()
        Story.objects.filter(site=self.site).delete()
        Story.objects.filter(site=self.shared_media_site).delete()

    def clear_media(self):
        Image.objects.filter(site=self.site).delete()
        Image.objects.filter(site=self.shared_media_site).delete()
        Audio.objects.filter(site=self.site).delete()
        Audio.objects.filter(site=self.shared_media_site).delete()
        Video.objects.filter(site=self.site).delete()
        Video.objects.filter(site=self.shared_media_site).delete()
        Document.objects.filter(site=self.site).delete()
        Document.objects.filter(site=self.shared_media_site).delete()

    def setup_method(self):
        if not AppJson.objects.filter(key="default_g2p_config").exists():
            call_command("loaddata", "default_g2p_config.json", app_label="backend")

        self.client = APIClient()
        self.admin_user = factories.get_app_admin(AppRole.STAFF)
        self.site = Site.objects.create(
            slug="sample",
            title="Sample Site",
            visibility=Visibility.PUBLIC,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.shared_media_site = Site.objects.create(
            slug="shared-media-site",
            title="Shared Media Site",
            is_hidden=True,
            visibility=Visibility.PUBLIC,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        factories.SiteFeatureFactory.create(
            key="shared_media",
            site=self.shared_media_site,
            is_enabled=True,
        )

    def teardown_method(self):
        self.clear_entries()
        self.clear_media()

        SiteFeature.objects.filter(site=self.shared_media_site).delete()
        Site.objects.filter(id=self.shared_media_site.id).delete()
        Site.objects.filter(id=self.site.id).delete()

    def get_search_response_types(self, types):
        url = reverse(
            "api:site-search-list", current_app="backend", args=[self.site.slug]
        )
        response = self.client.get(f"{url}?types={types}")
        return response

    def get_search_response_shared_media(self, types):
        url = reverse("api:search-list", current_app="backend")
        response = self.client.get(f"{url}?types={types}&hasSiteFeature=SHARED_MEDIA")
        return response

    def setup_entries(self):
        # If there are any entries from previous tests
        self.clear_entries()

        self.entry_public = factories.DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Public Entry",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.entry_members = factories.DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.MEMBERS,
            title="Members Entry",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.entry_team = factories.DictionaryEntryFactory.create(
            site=self.site,
            visibility=Visibility.TEAM,
            title="Team Entry",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )

    def setup_songs_and_stories(self):
        # If there are any songs/stories from previous tests
        self.clear_entries()

        self.song_public = factories.SongFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Public Song",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.song_members = factories.SongFactory.create(
            site=self.site,
            visibility=Visibility.MEMBERS,
            title="Members Song",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.song_team = factories.SongFactory.create(
            site=self.site,
            visibility=Visibility.TEAM,
            title="Team Song",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.story_public = factories.StoryFactory.create(
            site=self.site,
            visibility=Visibility.PUBLIC,
            title="Public Story",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.story_members = factories.StoryFactory.create(
            site=self.site,
            visibility=Visibility.MEMBERS,
            title="Members Story",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.story_team = factories.StoryFactory.create(
            site=self.site,
            visibility=Visibility.TEAM,
            title="Team Story",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )

    def setup_media(self):
        # If there is any media from previous tests
        self.clear_media()

        self.image = factories.ImageFactory.create(
            site=self.site,
            title="Image",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.audio = factories.AudioFactory.create(
            site=self.site,
            title="Audio",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.video = factories.VideoFactory.create(
            site=self.site,
            title="Video",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.document = factories.DocumentFactory.create(
            site=self.site,
            title="Document",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )

    def setup_shared_media(self):
        # If there is any media from previous tests
        self.clear_media()

        self.shared_image = factories.ImageFactory.create(
            site=self.shared_media_site,
            title="Shared Image",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.shared_audio = factories.AudioFactory.create(
            site=self.shared_media_site,
            title="Shared Audio",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.shared_video = factories.VideoFactory.create(
            site=self.shared_media_site,
            title="Shared Video",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.shared_document = factories.DocumentFactory.create(
            site=self.shared_media_site,
            title="Shared Document",
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )

    def assert_all_entries_visible(self, response):
        assert response.status_code == 200
        response = response.json()

        assert response["count"] == 3
        returned_ids = {result["entry"]["id"] for result in response["results"]}
        assert str(self.entry_public.id) in returned_ids
        assert str(self.entry_members.id) in returned_ids
        assert str(self.entry_team.id) in returned_ids

    def assert_all_songs_stories_visible(self, response):
        assert response.status_code == 200
        response = response.json()

        assert response["count"] == 6
        returned_ids = {result["entry"]["id"] for result in response["results"]}
        assert str(self.song_public.id) in returned_ids
        assert str(self.song_members.id) in returned_ids
        assert str(self.song_team.id) in returned_ids
        assert str(self.story_public.id) in returned_ids
        assert str(self.story_members.id) in returned_ids
        assert str(self.story_team.id) in returned_ids

    def assert_all_media_visible(self, response):
        assert response.status_code == 200
        response = response.json()

        assert response["count"] == 4
        returned_ids = {result["entry"]["id"] for result in response["results"]}
        assert str(self.image.id) in returned_ids
        assert str(self.audio.id) in returned_ids
        assert str(self.video.id) in returned_ids
        assert str(self.document.id) in returned_ids

    def test_entry_permissions_anonymous(self):
        self.setup_entries()
        user = factories.get_anonymous_user()
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("word,phrase")
        assert response.status_code == 200
        response = response.json()

        assert response["count"] == 1
        assert response["results"][0]["entry"]["id"] == str(self.entry_public.id)

    def test_entry_permissions_member(self):
        self.setup_entries()
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(site=self.site, user=user, role=Role.MEMBER)
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("word,phrase")
        assert response.status_code == 200
        response = response.json()

        assert response["count"] == 2
        returned_ids = {result["entry"]["id"] for result in response["results"]}
        assert str(self.entry_public.id) in returned_ids
        assert str(self.entry_members.id) in returned_ids

    def test_entry_permissions_team(self):
        self.setup_entries()
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            site=self.site, user=user, role=Role.ASSISTANT
        )
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("word,phrase")
        self.assert_all_entries_visible(response)

    @pytest.mark.parametrize("app_role", [AppRole.STAFF, AppRole.SUPERADMIN])
    def test_entry_permissions_app_admin(self, app_role):
        self.setup_entries()
        user = factories.get_app_admin(app_role)
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("word,phrase")
        self.assert_all_entries_visible(response)

    def test_song_story_permissions_anonymous(self):
        self.setup_songs_and_stories()
        user = factories.get_anonymous_user()
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("song,story")
        assert response.status_code == 200
        response = response.json()

        assert response["count"] == 2
        returned_ids = {result["entry"]["id"] for result in response["results"]}
        assert str(self.song_public.id) in returned_ids
        assert str(self.story_public.id) in returned_ids

    def test_song_story_permissions_member(self):
        self.setup_songs_and_stories()
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(site=self.site, user=user, role=Role.MEMBER)
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("song,story")
        assert response.status_code == 200
        response = response.json()

        assert response["count"] == 4
        returned_ids = {result["entry"]["id"] for result in response["results"]}
        assert str(self.song_public.id) in returned_ids
        assert str(self.song_members.id) in returned_ids
        assert str(self.story_public.id) in returned_ids
        assert str(self.story_members.id) in returned_ids

    def test_song_story_permissions_team(self):
        self.setup_songs_and_stories()
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            site=self.site, user=user, role=Role.ASSISTANT
        )
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("song,story")
        self.assert_all_songs_stories_visible(response)

    @pytest.mark.parametrize("app_role", [AppRole.STAFF, AppRole.SUPERADMIN])
    def test_song_story_permissions_app_admin(self, app_role):
        self.setup_songs_and_stories()
        user = factories.get_app_admin(app_role)
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("song,story")
        self.assert_all_songs_stories_visible(response)

    @pytest.mark.parametrize(
        "user_role",
        [None, Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    def test_media_permissions_public_site(self, user_role):
        self.setup_media()
        user = factories.get_non_member_user()
        if user_role:
            factories.MembershipFactory.create(
                site=self.site, user=user, role=user_role
            )
        self.client.force_authenticate(user=user)

        response = self.get_search_response_types("image,audio,video,document")
        self.assert_all_media_visible(response)

    @pytest.mark.parametrize(
        "user_role",
        [None, Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.parametrize("site_visibility", [Visibility.MEMBERS, Visibility.TEAM])
    def test_media_permissions_non_public_site(self, user_role, site_visibility):
        self.site.visibility = site_visibility
        self.site.save()
        self.setup_media()
        user = factories.get_non_member_user()
        if user_role:
            factories.MembershipFactory.create(
                site=self.site, user=user, role=user_role
            )
        self.client.force_authenticate(user=user)
        response = self.get_search_response_types("image,audio,video,document")
        if user_role in [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]:
            self.assert_all_media_visible(response)
        else:
            assert response.status_code == 403

    @pytest.mark.parametrize(
        "user_role",
        [None, Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    def test_shared_media_permissions(self, user_role):
        self.setup_shared_media()
        user = factories.get_non_member_user()
        if user_role:
            factories.MembershipFactory.create(
                site=self.shared_media_site, user=user, role=user_role
            )
        self.client.force_authenticate(user=user)

        response = self.get_search_response_shared_media("image,audio,video,document")
        assert response.status_code == 200
        response = response.json()

        returned_ids = {result["entry"]["id"] for result in response["results"]}
        assert str(self.shared_image.id) in returned_ids
        assert str(self.shared_audio.id) in returned_ids
        assert str(self.shared_video.id) in returned_ids
        assert str(self.shared_document.id) in returned_ids
