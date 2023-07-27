from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedIdentityField

from ..models import Membership
from ..models.constants import Role, Visibility
from . import fields
from .utils import get_site_from_context

base_timestamp_fields = ("created", "last_modified")
base_id_fields = ("id", "title", "url")


class SiteContentUrlMixin:
    """
    Mixin to configure url identity field for site content models
    """

    serializer_url_field = fields.SiteHyperlinkedIdentityField

    def build_url_field(self, field_name, model_class):
        """
        Add our namespace to the view_name
        """
        field_class, field_kwargs = super().build_url_field(field_name, model_class)
        field_kwargs["view_name"] = "api:" + field_kwargs["view_name"]

        return field_class, field_kwargs


class ExternalSiteContentUrlMixin(SiteContentUrlMixin):
    """
    Mixin to configure url identity field for site content models from other sites.
    """

    serializer_url_field = NestedHyperlinkedIdentityField

    def build_url_field(self, field_name, model_class):
        """
        Add our namespace to the view_name
        """
        field_class, field_kwargs = super().build_url_field(field_name, model_class)
        field_kwargs["parent_lookup_kwargs"] = {"site_slug": "site__slug"}

        return field_class, field_kwargs


class SiteContentLinkedTitleSerializer(
    SiteContentUrlMixin, serializers.ModelSerializer
):
    """
    Serializer that produces standard id-title-url objects for site content models.
    """

    id = serializers.UUIDField(read_only=True)

    class Meta:
        fields = base_id_fields


class UpdateSerializerMixin:
    """
    A mixin for ModelSerializers that sets the required fields for subclasses of BaseModel
    """

    def update(self, instance, validated_data):
        validated_data["last_modified_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class CreateSerializerMixin:
    """
    A mixin for ModelSerializers that sets the required fields for subclasses of BaseModel
    """

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["last_modified_by"] = self.context["request"].user
        return super().create(validated_data)


class CreateSiteContentSerializerMixin(CreateSerializerMixin):
    """
    A mixin for ModelSerializers that sets the required fields for subclasses of BaseSiteContentModel
    """

    def create(self, validated_data):
        validated_data["site"] = get_site_from_context(self)
        return super().create(validated_data)


class CreateControlledSiteContentSerializerMixin(CreateSiteContentSerializerMixin):
    """
    A mixin for ModelSerializers that sets the required fields for subclasses of BaseControlledModel
    """

    def validate(self, attrs):
        site = get_site_from_context(self)
        user = self.context["request"].user
        memberships = Membership.objects.filter(user=user)

        visibility = attrs.get("visibility")

        site_membership = memberships.filter(site=site).first()
        if site_membership:
            if site_membership.role == Role.ASSISTANT and visibility > Visibility.TEAM:
                raise serializers.ValidationError(
                    "Assistants cannot change the visibility of controlled content."
                )

        return super().validate(attrs)


class WritableVisibilityField(serializers.CharField):
    def to_internal_value(self, data):
        visibility_map = {choice[1].lower(): choice[0] for choice in Visibility.choices}
        try:
            return visibility_map[data.lower()]
        except KeyError:
            raise serializers.ValidationError("Invalid visibility option.")

    def to_representation(self, value):
        visibility_map = {choice[0]: choice[1] for choice in Visibility.choices}
        try:
            return visibility_map[value]
        except KeyError:
            raise serializers.ValidationError("Invalid visibility value.")
