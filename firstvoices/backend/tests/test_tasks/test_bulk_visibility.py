import uuid
from unittest.mock import patch

import pytest

from backend.models import DictionaryEntry, SitePage, Song, Story, StoryPage
from backend.models.constants import Visibility
from backend.models.jobs import BulkVisibilityJob, JobStatus
from backend.models.widget import SiteWidget
from backend.tasks.visibility_tasks import bulk_change_visibility
from backend.tests import factories
from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin


class TestBulkVisibilityTasks(IgnoreTaskResultsMixin):
    TASK = bulk_change_visibility

    def get_valid_task_args(self):
        return (uuid.uuid4(),)

    @pytest.fixture(scope="function", autouse=True)
    def mocked_indexing_async_func(self, mocker):
        self.mocked_func = mocker.patch(
            "backend.tasks.visibility_tasks.request_sync_all_site_content_in_indexes"
        )

    @pytest.mark.django_db
    def test_bulk_visibility_change_job_invalid_id(self, caplog):
        invalid_id = uuid.uuid4()
        with pytest.raises(BulkVisibilityJob.DoesNotExist):
            bulk_change_visibility(invalid_id)

        assert (
            f"Task started. Additional info: job_instance_id: {invalid_id}"
            in caplog.text
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "from_visibility, to_visibility, existing_feature",
        [
            (Visibility.PUBLIC, Visibility.MEMBERS, True),
            (Visibility.PUBLIC, Visibility.MEMBERS, False),
            (Visibility.MEMBERS, Visibility.PUBLIC, True),
            (Visibility.MEMBERS, Visibility.PUBLIC, False),
            (Visibility.TEAM, Visibility.MEMBERS, True),
            (Visibility.TEAM, Visibility.MEMBERS, False),
            (Visibility.MEMBERS, Visibility.TEAM, True),
            (Visibility.MEMBERS, Visibility.TEAM, False),
        ],
    )
    def test_bulk_visibility_change_job_site_only(
        self, from_visibility, to_visibility, existing_feature, caplog
    ):
        site = factories.SiteFactory.create(visibility=from_visibility)
        job = factories.BulkVisibilityJobFactory.create(
            site=site, from_visibility=from_visibility, to_visibility=to_visibility
        )
        if existing_feature:
            factories.SiteFeatureFactory.create(
                site=site, key="indexing_paused", is_enabled=True
            )
        bulk_change_visibility(job.id)

        job.refresh_from_db()
        site.refresh_from_db()

        assert job.status == JobStatus.COMPLETE
        assert site.visibility == to_visibility
        assert site.sitefeature_set.get(key="indexing_paused").is_enabled is False
        assert self.mocked_func.call_count == 1

        assert (
            f"Task started. Additional info: job_instance_id: {job.id}" in caplog.text
        )
        assert "Task ended." in caplog.text

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "from_visibility, to_visibility",
        [
            (Visibility.PUBLIC, Visibility.MEMBERS),
            (Visibility.MEMBERS, Visibility.PUBLIC),
            (Visibility.TEAM, Visibility.MEMBERS),
            (Visibility.MEMBERS, Visibility.TEAM),
        ],
    )
    def test_bulk_visibility_change_job_full(
        self, from_visibility, to_visibility, caplog
    ):
        site = factories.SiteFactory.create(visibility=from_visibility)
        existing_widgets = SiteWidget.objects.filter(
            site=site, visibility=from_visibility
        ).count()
        factories.DictionaryEntryFactory.create_batch(
            10, site=site, visibility=from_visibility
        )
        factories.SongFactory.create_batch(10, site=site, visibility=from_visibility)
        stories = factories.StoryFactory.create_batch(
            10, site=site, visibility=from_visibility
        )
        for story in stories:
            factories.StoryPageFactory.create_batch(
                3, story=story, visibility=from_visibility
            )
        factories.SitePageFactory.create_batch(
            10, site=site, visibility=from_visibility
        )
        factories.SiteWidgetFactory.create_batch(
            10, site=site, visibility=from_visibility
        )

        job = factories.BulkVisibilityJobFactory.create(
            site=site, from_visibility=from_visibility, to_visibility=to_visibility
        )
        bulk_change_visibility(job.id)

        job.refresh_from_db()
        site.refresh_from_db()

        assert job.status == JobStatus.COMPLETE
        assert site.visibility == to_visibility
        assert site.sitefeature_set.get(key="indexing_paused").is_enabled is False
        assert self.mocked_func.call_count == 1

        assert (
            DictionaryEntry.objects.filter(site=site, visibility=to_visibility).count()
            == 10
        )
        assert Song.objects.filter(site=site, visibility=to_visibility).count() == 10
        assert Story.objects.filter(site=site, visibility=to_visibility).count() == 10
        assert (
            StoryPage.objects.filter(site=site, visibility=to_visibility).count() == 30
        )
        assert (
            SitePage.objects.filter(site=site, visibility=to_visibility).count() == 10
        )
        assert (
            SiteWidget.objects.filter(site=site, visibility=to_visibility).count()
            == 10 + existing_widgets
        )

        assert (
            f"Task started. Additional info: job_instance_id: {job.id}" in caplog.text
        )
        assert "Task ended." in caplog.text

    @pytest.mark.django_db
    def test_bulk_visibility_change_job_exception(self, caplog):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.DictionaryEntryFactory.create_batch(
            10, site=site, visibility=Visibility.PUBLIC
        )
        job = factories.BulkVisibilityJobFactory.create(
            site=site,
            from_visibility=Visibility.PUBLIC,
            to_visibility=Visibility.MEMBERS,
        )

        with patch(
            "django.db.models.query.QuerySet.update",
            side_effect=Exception("Mocked exception"),
        ):
            bulk_change_visibility(job.id)

            job.refresh_from_db()
            site.refresh_from_db()

            assert job.status == JobStatus.FAILED
            assert site.visibility == Visibility.PUBLIC
            assert site.sitefeature_set.get(key="indexing_paused").is_enabled is False
            assert self.mocked_func.call_count == 0
            assert (
                DictionaryEntry.objects.filter(
                    site=site, visibility=Visibility.MEMBERS
                ).count()
                == 0
            )
            assert (
                DictionaryEntry.objects.filter(
                    site=site, visibility=Visibility.PUBLIC
                ).count()
                == 10
            )

        assert (
            f"Task started. Additional info: job_instance_id: {job.id}" in caplog.text
        )
        assert "Mocked exception" in caplog.text
        assert "Task ended." in caplog.text

    @pytest.mark.django_db
    def test_bulkvisiblilityjob_not_triggered_while_running(self, caplog):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.DictionaryEntryFactory.create_batch(
            10, site=site, visibility=Visibility.PUBLIC
        )
        factories.BulkVisibilityJobFactory.create(
            site=site,
            from_visibility=Visibility.PUBLIC,
            to_visibility=Visibility.MEMBERS,
            status=JobStatus.STARTED,
        )
        job = factories.BulkVisibilityJobFactory.create(
            site=site,
            from_visibility=Visibility.PUBLIC,
            to_visibility=Visibility.MEMBERS,
        )
        bulk_change_visibility(job.id)

        job.refresh_from_db()
        site.refresh_from_db()

        assert job.status == JobStatus.CANCELLED
        assert job.message == (
            "Job cancelled as another bulk visibility job is already in progress for the same site."
        )
        assert site.visibility == Visibility.PUBLIC
        assert (
            DictionaryEntry.objects.filter(
                site=site, visibility=Visibility.MEMBERS
            ).count()
            == 0
        )
        assert (
            DictionaryEntry.objects.filter(
                site=site, visibility=Visibility.PUBLIC
            ).count()
            == 10
        )

        assert (
            f"Task started. Additional info: job_instance_id: {job.id}" in caplog.text
        )
        assert (
            "Job cancelled as another bulk visibility job is already in progress for the same site."
            in caplog.text
        )
        assert "Task ended." in caplog.text
