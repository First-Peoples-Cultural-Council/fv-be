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
from backend.serializers.validators import MeetsSiteVisibility, SameSite


class ImmersionLabelDetailSerializer(WritableSiteContentSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:immersionlabel-detail", read_only=True, lookup_field="key"
    )
    dictionary_entry = WritableRelatedDictionaryEntrySerializer(
        required=True,
        queryset=DictionaryEntry.objects.all(),
        validators=[SameSite(), MeetsSiteVisibility()],
    )
    key = serializers.CharField(allow_blank=False, allow_null=False)

    def update(self, instance, validated_data):
        """
        Override update to make key read only after creation.
        """
        validated_data.pop("key", None)
        return super().update(instance, validated_data)

    class Meta:
        model = ImmersionLabel
        fields = base_timestamp_fields + (
            "id",
            "url",
            "site",
            "dictionary_entry",
            "key",
        )
