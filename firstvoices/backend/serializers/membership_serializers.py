from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from backend.models import Membership
from backend.models.constants import Role
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_timestamp_fields,
)
from backend.serializers.fields import EnumField, SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import ImageSerializer
from backend.serializers.site_serializers import (
    FeatureFlagSerializer,
    SiteSummarySerializer,
)
from backend.serializers.user_serializers import UserDetailSerializer
from backend.serializers.validators import UniqueForSite


class MembershipSiteSummarySerializer(serializers.HyperlinkedModelSerializer):
    """
    Summary information about the site of a given Membership, as well as the role info.
    """

    id = serializers.UUIDField(source="site.id")
    role = serializers.CharField(source="get_role_display")
    url = serializers.SerializerMethodField()
    title = serializers.CharField(source="site.title")
    slug = serializers.CharField(source="site.slug")
    language = serializers.StringRelatedField(source="site.language")
    visibility = serializers.CharField(source="site.get_visibility_display")
    logo = ImageSerializer(source="site.logo")
    enabled_features = FeatureFlagSerializer(
        read_only=True, source="site.sitefeature_set", many=True
    )
    is_hidden = serializers.BooleanField(source="site.is_hidden")

    def get_url(self, instance):
        # the lookup_field of the HyperlinkedIdentityField doesn't handle related fields,
        # so we reverse the url ourselves
        return reverse(
            "api:my-sites-detail",
            current_app="backend",
            args=[instance.site.slug],
            request=self.context["request"],
        )

    def to_representation(self, instance):
        """Covert visibility to lowercase"""
        site = super().to_representation(instance)
        site["visibility"] = site["visibility"].lower()
        return site

    class Meta:
        model = Membership
        fields = ("role",) + SiteSummarySerializer.Meta.fields


class WriteableUserEmailSerializer(serializers.SlugRelatedField):
    def to_representation(self, value):
        return UserDetailSerializer(context=self.context).to_representation(value)


class MembershipDetailSerializer(WritableSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(
        read_only=True, view_name="api:membership-detail"
    )
    user = WriteableUserEmailSerializer(
        allow_null=False,
        slug_field="email",
        queryset=get_user_model().objects.all(),
        validators=[UniqueForSite(queryset=Membership.objects.all())],
    )
    role = EnumField(enum=Role)

    def update(self, instance, validated_data):
        """
        Override update to make user read only after creation.
        """
        validated_data.pop("user", None)
        return super().update(instance, validated_data)

    class Meta:
        model = Membership

        fields = base_timestamp_fields + (
            "id",
            "site",
            "url",
            "role",
            "user",
        )
