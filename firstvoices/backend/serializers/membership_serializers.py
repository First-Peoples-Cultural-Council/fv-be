from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from backend.models import Membership
from backend.models.constants import Role
from backend.serializers.base_serializers import UpdateSerializerMixin, CreateSiteContentSerializerMixin, SiteContentUrlMixin
from backend.serializers.fields import PrimaryKeyInputField
from backend.serializers.media_serializers import ImageSerializer
from backend.serializers.site_serializers import (
    FeatureFlagSerializer,
    SiteSummarySerializer,
)
from backend.serializers import fields


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
    features = FeatureFlagSerializer(source="site.sitefeature_set", many=True)

    def get_url(self, instance):
        # the lookup_field of the HyperlinkedIdentityField doesn't handle related fields,
        # so we reverse the url ourselves
        return reverse(
            "api:my-sites-detail",
            current_app="backend",
            args=[instance.site.slug],
            request=self.context["request"],
        )

    class Meta:
        model = Membership
        fields = ("role",) + SiteSummarySerializer.Meta.fields


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ("id", "email")


class MembershipSerializer(UpdateSerializerMixin,
                           CreateSiteContentSerializerMixin,
                           SiteContentUrlMixin, serializers.HyperlinkedModelSerializer):

    user = PrimaryKeyInputField(output_serializer=UserSerializer, queryset=get_user_model().objects.all())
    role = fields.EnumField(enum=Role)

    class Meta:
        model = Membership
        fields = ("id", "url", "role", "user", "created")
