import factory
from factory.django import DjangoModelFactory

from backend.models import AppJson


class AppJsonFactory(DjangoModelFactory):
    class Meta:
        model = AppJson

    key = factory.Sequence(lambda n: "AppJson %03d" % n)
    json = factory.Sequence(lambda n: "{ 'value': %03d }" % n)
