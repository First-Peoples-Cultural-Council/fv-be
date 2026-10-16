from rest_framework import serializers

"""
The serializers in this file are only used in the API docs for site statistics. They are not used in the actual
view.
"""


class HealthMetricsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    completion_percentage = serializers.IntegerField()


class EntryHealthMetricsSerializer(serializers.Serializer):
    entries_without_audio = HealthMetricsSerializer()
    entries_without_categories = HealthMetricsSerializer()
    entries_without_images = HealthMetricsSerializer()
    entries_without_related_entries = HealthMetricsSerializer()
    entries_without_translations = HealthMetricsSerializer()


class CharacterHealthMetricsSerializer(serializers.Serializer):
    characters_without_audio = HealthMetricsSerializer()
    characters_without_images = HealthMetricsSerializer()
    characters_without_related_entries = HealthMetricsSerializer()


class SiteHealthMetricsSerializer(serializers.Serializer):
    entries = EntryHealthMetricsSerializer()
    characters = CharacterHealthMetricsSerializer()
