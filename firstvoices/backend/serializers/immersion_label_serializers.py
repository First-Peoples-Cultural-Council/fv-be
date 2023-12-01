from rest_framework import serializers

from backend.models import DictionaryEntry
from backend.models.immersion_labels import ImmersionLabel
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_timestamp_fields,
)
from backend.serializers.dictionary_serializers import (
    WritableRelatedDictionaryEntrySerializer,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField


class ImmersionLabelDetailSerializer(WritableSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:immersionlabel-detail", read_only=True, lookup_field="key"
    )
    dictionary_entry = WritableRelatedDictionaryEntrySerializer(
        required=True,
        queryset=DictionaryEntry.objects.all(),
    )
    key = serializers.CharField(allow_blank=False, allow_null=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        site = self.context["site"]
        dictionary_entry = attrs.get("dictionary_entry")

        if dictionary_entry:
            if dictionary_entry.site != site:
                raise serializers.ValidationError(
                    "Dictionary entry must belong to the same site as the immersion label."
                )

        return attrs

    class Meta:
        model = ImmersionLabel
        fields = base_timestamp_fields + (
            "id",
            "url",
            "site",
            "dictionary_entry",
            "key",
        )
