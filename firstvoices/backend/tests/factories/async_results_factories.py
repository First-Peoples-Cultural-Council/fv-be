import factory
from factory.django import DjangoModelFactory

from backend.models import CustomOrderRecalculationResult
from backend.tests.factories.access import SiteFactory, UserFactory


class CustomOrderRecalculationPreviewResultFactory(DjangoModelFactory):
    class Meta:
        model = CustomOrderRecalculationResult

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    latest_recalculation_result = {"test": "test"}
