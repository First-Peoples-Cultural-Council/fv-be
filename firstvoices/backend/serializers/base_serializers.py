from django.core.exceptions import PermissionDenied
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedIdentityField

from ..models import Membership, Site
from ..models.constants import Role, Visibility
from . import fields
from .fields import WritableVisibilityField
from .utils import get_site_from_context

base_timestamp_fields = ("created", "created_by", "last_modified", "last_modified_by")
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
                raise PermissionDenied(
                    "Assistants cannot create or edit published content."
                )

        return super().validate(attrs)


class ReadOnlyVisibilityFieldMixin:
    """
    A mixin for ModelSerializers that provides a read-only visibility field.
    """

    visibility = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    @extend_schema_field(OpenApiTypes.STR)
    def get_visibility(instance):
        return instance.get_visibility_display().lower()


class LinkedSiteSerializer(
    serializers.HyperlinkedModelSerializer, ReadOnlyVisibilityFieldMixin
):
    """
    Minimal info about a site, suitable for serializing a site as a related field.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="api:site-detail", lookup_field="slug"
    )
    language = serializers.StringRelatedField()
    visibility = serializers.SerializerMethodField(read_only=True)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Site
        fields = base_id_fields + ("slug", "visibility", "language")


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

    class Meta:
        fields = base_timestamp_fields + base_id_fields + ("site",)


class WritableSiteContentSerializer(
    CreateSiteContentSerializerMixin,
    UpdateSerializerMixin,
    BaseSiteContentSerializer,
):
    """
    Writable serializer for site content models.
    """

    class Meta(BaseSiteContentSerializer.Meta):
        fields = BaseSiteContentSerializer.Meta.fields


class BaseControlledSiteContentSerializer(
    BaseSiteContentSerializer, ReadOnlyVisibilityFieldMixin
):
    """
    Base serializer for controlled site content models.
    """

    visibility = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = BaseSiteContentSerializer.Meta.fields + ("visibility",)


class WritableControlledSiteContentSerializer(
    CreateControlledSiteContentSerializerMixin,
    UpdateSerializerMixin,
    BaseControlledSiteContentSerializer,
):
    """
    Writable serializer for controlled site content models.
    """

    visibility = WritableVisibilityField(required=True)

    class Meta(BaseControlledSiteContentSerializer.Meta):
        fields = BaseControlledSiteContentSerializer.Meta.fields
