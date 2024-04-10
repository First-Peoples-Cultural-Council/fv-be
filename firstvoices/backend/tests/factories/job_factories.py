import factory
from factory.django import DjangoModelFactory

from backend.models import BulkVisibilityJob, CustomOrderRecalculationResult
from backend.tests.factories.access import SiteFactory, UserFactory


class CustomOrderRecalculationResultFactory(DjangoModelFactory):
    class Meta:
        model = CustomOrderRecalculationResult

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    latest_recalculation_result = {"test": "test"}


class BulkVisibilityJobFactory(DjangoModelFactory):
    class Meta:
        model = BulkVisibilityJob

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    task_id = factory.sequence(lambda n: f"task_id_{n}")
