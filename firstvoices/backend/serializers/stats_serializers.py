from rest_framework import serializers

"""
The serializers in this file are only used in the API docs for site statistics. They are not used in the actual
view.
"""


class AggregateItemSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    availableInChildrensArchive = serializers.IntegerField()


class AggregateControlledItemSerializer(AggregateItemSerializer):
    public = serializers.IntegerField()
    members = serializers.IntegerField()
    team = serializers.IntegerField()


class AggregateSerializer(serializers.Serializer):
    words = AggregateControlledItemSerializer()
    phrases = AggregateControlledItemSerializer()
    songs = AggregateControlledItemSerializer()
    stories = AggregateControlledItemSerializer()
    audio = AggregateItemSerializer()
    document = AggregateItemSerializer()
    images = AggregateItemSerializer()
    video = AggregateItemSerializer()


class TemporalStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()


class TemporalControlledStatsSerializer(TemporalStatsSerializer):
    public = serializers.IntegerField()
    members = serializers.IntegerField()
    team = serializers.IntegerField()


class TemporalTimePeriodSerializer(serializers.Serializer):
    created = TemporalStatsSerializer()
    lastModified = TemporalStatsSerializer()


class TemporalControlledTimePeriodSerializer(TemporalTimePeriodSerializer):
    created = TemporalControlledStatsSerializer()
    lastModified = TemporalControlledStatsSerializer()


class TemporalTimeRangesSerializer(serializers.Serializer):
    lastYear = TemporalTimePeriodSerializer()
    last6Months = TemporalTimePeriodSerializer()
    last3Months = TemporalTimePeriodSerializer()
    lastMonth = TemporalTimePeriodSerializer()
    lastWeek = TemporalTimePeriodSerializer()
    last3Days = TemporalTimePeriodSerializer()
    today = TemporalTimePeriodSerializer()


class TemporalControlledTimeRangesSerializer(TemporalTimeRangesSerializer):
    lastYear = TemporalControlledTimePeriodSerializer()
    last6Months = TemporalControlledTimePeriodSerializer()
    last3Months = TemporalControlledTimePeriodSerializer()
    lastMonth = TemporalControlledTimePeriodSerializer()
    lastWeek = TemporalControlledTimePeriodSerializer()
    last3Days = TemporalControlledTimePeriodSerializer()
    today = TemporalControlledTimePeriodSerializer()


class TemporalSerializer(serializers.Serializer):
    words = TemporalControlledTimeRangesSerializer()
    phrases = TemporalControlledTimeRangesSerializer()
    songs = TemporalControlledTimeRangesSerializer()
    stories = TemporalControlledTimeRangesSerializer()
    audio = TemporalTimeRangesSerializer()
    document = TemporalTimeRangesSerializer()
    images = TemporalTimeRangesSerializer()
    video = TemporalTimeRangesSerializer()


class SiteStatsSerializer(serializers.Serializer):
    aggregate = AggregateSerializer()
    temporal = TemporalSerializer()
