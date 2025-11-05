import uuid

from django.core.exceptions import PermissionDenied
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_nested.relations import NestedHyperlinkedIdentityField

from backend.serializers.utils.context_utils import get_site_from_context

from ..models import Membership, Site
from ..models.constants import Role, Visibility
from . import fields
from .fields import WritableVisibilityField

base_timestamp_fields = (
    "created",
    "created_by",
    "last_modified",
    "last_modified_by",
    "system_last_modified",
    "system_last_modified_by",
)
base_id_fields = ("id", "url", "title")
audience_fields = ("exclude_from_games", "exclude_from_kids")


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
        validated_data["system_last_modified_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class CreateSerializerMixin:
    """
    A mixin for ModelSerializers that sets the required fields for subclasses of BaseModel
    """

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["last_modified_by"] = self.context["request"].user
        validated_data["system_last_modified_by"] = self.context["request"].user
        return super().create(validated_data)


class CreateSiteContentSerializerMixin(CreateSerializerMixin):
    """
    A mixin for ModelSerializers that sets the required fields for subclasses of BaseSiteContentModel
    """

    def create(self, validated_data):
        validated_data["site"] = get_site_from_context(self)
        return super().create(validated_data)


class ValidateAssistantWritePermissionMixin:
    """
    A mixin for ModelSerializers that validates the Assistant write permission based on the submitted
    visibility level. Compatible with POST, PUT, and PATCH style writes.
    """

    def validate(self, attrs):
        attrs = super().validate(attrs)

        site = get_site_from_context(self)
        user = self.context["request"].user
        memberships = Membership.objects.filter(user=user)
        site_membership = memberships.filter(site=site).first()

        if site_membership and site_membership.role == Role.ASSISTANT:
            visibility = attrs.get("visibility")
            # This condition is written to allow PATCH to send an empty visibility value
            if visibility == Visibility.MEMBERS or visibility == Visibility.PUBLIC:
                raise PermissionDenied(
                    "Assistants cannot create or edit published content."
                )

        return attrs


class ReadOnlyVisibilityFieldMixin(metaclass=serializers.SerializerMetaclass):
    """
    A mixin for ModelSerializers that provides a read-only visibility field.
    """

    visibility = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_visibility(instance):
        return instance.get_visibility_display().lower()

    class Meta:
        fields = ("visibility",)


class ValidateNonNullableCharFieldsMixin:
    """
    A mixin for ModelSerializers that replaces null values with an empty string for char fields.
    """

    def validate(self, attrs):
        for field_name, field in self.fields.items():
            if isinstance(field, serializers.CharField):
                if field_name in attrs and attrs.get(field_name) is None:
                    attrs[field_name] = ""

        return super().validate(attrs)


class LinkedSiteSerializer(
    ReadOnlyVisibilityFieldMixin, serializers.HyperlinkedModelSerializer
):
    """
    Info about a linked site, suitable for serializing a site as a related field.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="api:site-detail", lookup_field="slug"
    )
    language = serializers.StringRelatedField()
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Site
        fields = base_id_fields + ("slug", "visibility", "language")


class LinkedSiteMinimalSerializer(
    ReadOnlyVisibilityFieldMixin, serializers.ModelSerializer
):
    """
    Minimal info about a site, suitable for search results.
    """

    is_hidden = serializers.BooleanField(read_only=True)

    class Meta:
        model = Site
        fields = ("id", "slug", "title", "visibility", "is_hidden")
        read_only_fields = ("id", "slug", "title", "is_hidden")


class BaseSiteContentSerializer(SiteContentLinkedTitleSerializer):
    """
    Base serializer for site content models.
    """

    id = serializers.UUIDField(read_only=True)
    site = LinkedSiteSerializer(read_only=True)

    created = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    last_modified = serializers.DateTimeField(read_only=True)
    last_modified_by = serializers.StringRelatedField(read_only=True)
    system_last_modified = serializers.DateTimeField(read_only=True)
    system_last_modified_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        fields = base_timestamp_fields + base_id_fields + ("site",)


class WritableSiteContentSerializer(
    CreateSiteContentSerializerMixin,
    UpdateSerializerMixin,
    ValidateNonNullableCharFieldsMixin,
    BaseSiteContentSerializer,
):
    """
    Writable serializer for site content models.
    """

    class Meta(BaseSiteContentSerializer.Meta):
        fields = BaseSiteContentSerializer.Meta.fields


class BaseControlledSiteContentSerializer(
    ReadOnlyVisibilityFieldMixin, BaseSiteContentSerializer
):
    """
    Base serializer for controlled site content models.
    """

    class Meta:
        fields = BaseSiteContentSerializer.Meta.fields + ("visibility",)


class WritableControlledSiteContentSerializer(
    ValidateAssistantWritePermissionMixin,
    ValidateNonNullableCharFieldsMixin,
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    BaseControlledSiteContentSerializer,
):
    """
    Writable serializer for controlled site content models.
    """

    visibility = WritableVisibilityField(required=True)

    class Meta(BaseControlledSiteContentSerializer.Meta):
        fields = BaseControlledSiteContentSerializer.Meta.fields


class ArbitraryIdSerializer(serializers.CharField):
    """
    Represent a text value as an object with an arbitrary id.
    """

    def to_representation(self, value):
        """
        Transform the *outgoing* native value into primitive data.
        """
        return {
            "id": str(uuid.uuid4()),
            "text": str(value),
        }

    def to_internal_value(self, data):
        """
        Transform the *incoming* primitive data into a native value.
        """
        try:
            text = data["text"]
            return super().to_internal_value(text)
        except KeyError as e:
            raise ValidationError(f"Expected an object with key {e}")
