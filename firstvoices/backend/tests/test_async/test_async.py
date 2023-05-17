import pytest

from backend.tasks.alphabet_tasks import recalculate_custom_order_preview
from backend.tests import factories


class TestCustomOrderRecalculatePreview:
    @pytest.fixture
    def celery_config(self):
        yield {
            "broker_url": "amqp://rabbitmq:rabbitmq@localhost:5672//fv",
            "result_backend": "redis://localhost/0",
        }

    @pytest.fixture
    def site(self):
        return factories.SiteFactory.create(slug="test")

    @pytest.fixture
    def alphabet(self, site):
        return factories.AlphabetFactory.create(site=site)

    @pytest.mark.django_db(transaction=True)
    def test_recalculate_preview_callback(self, celery_worker, site, alphabet):
        result = recalculate_custom_order_preview.apply_async(args=["test"])
        result.wait(timeout=10)
        assert result.status == "SUCCESS"
