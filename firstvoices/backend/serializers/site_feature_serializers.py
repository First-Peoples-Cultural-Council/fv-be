from rest_framework import serializers

from backend.models.sites import SiteFeature
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_timestamp_fields,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField


class SiteFeatureDetailSerializer(WritableSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitefeature-detail", read_only=True, lookup_field="key"
    )
    key = serializers.CharField(required=True, allow_blank=False)
    is_enabled = serializers.BooleanField(required=True, allow_null=False)

    def update(self, instance, validated_data):
        """
        Override update to make key read only after creation.
        """
        validated_data.pop("key", None)
        return super().update(instance, validated_data)

    def validate(self, attrs):
        """
        Validate that duplicate keys are not allowed.
        """
        attrs = super().validate(attrs)
        site = self.context["site"]
        key = attrs.get("key")

        if (
            SiteFeature.objects.filter(site=site, key=key).exists()
            and not self.instance
        ):
            raise serializers.ValidationError(
                {"key": "A feature flag with this key already exists for this site."}
            )
        return attrs

    class Meta:
        model = SiteFeature
        fields = base_timestamp_fields + (
            "id",
            "url",
            "site",
            "key",
            "is_enabled",
        )
