from rest_framework import serializers

from backend.models import Site

from . import fields
from .serializer_utils import get_site_from_context

base_timestamp_fields = ("created", "last_modified")
base_id_fields = ("id", "title", "url")


class SiteContentLinkedTitleSerializer(serializers.ModelSerializer):
    """
    Serializer that produces standard id-title-url objects for site content models.
    """

    serializer_url_field = fields.SiteHyperlinkedIdentityField

    id = serializers.UUIDField(read_only=True)

    def build_url_field(self, field_name, model_class):
        """
        Add our namespace to the view_name
        """
        field_class, field_kwargs = super().build_url_field(field_name, model_class)
        field_kwargs["view_name"] = "api:" + field_kwargs["view_name"]

        return field_class, field_kwargs

    class Meta:
        fields = base_id_fields


class UpdateSiteContentSerializerMixin:
    """
    A mixin for ModelSerializers that sets the required fields for subclasses of BaseSiteContentModel
    """

    def update(self, instance, validated_data):
        site_slug = get_site_from_context(self)
        validated_data["site"] = Site.objects.filter(slug=site_slug).first()
        validated_data["last_modified_by"] = self.context["request"].user
        return super().update(instance, validated_data)
