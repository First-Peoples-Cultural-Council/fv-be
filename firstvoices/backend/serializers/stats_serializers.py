from rest_framework import serializers

"""
The serializers in this file are only used in the API docs for site statistics. They are not used in the actual
view.
"""


class AggregateItemSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    availableInChildrensArchive = serializers.IntegerField()
    public = serializers.IntegerField()


class AggregateSerializer(serializers.Serializer):
    words = AggregateItemSerializer()
    phrases = AggregateItemSerializer()
    songs = AggregateItemSerializer()
    stories = AggregateItemSerializer()
    images = AggregateItemSerializer()
    audio = AggregateItemSerializer()
    video = AggregateItemSerializer()


class TemporalItemSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    lastModified = serializers.IntegerField()
    public = serializers.IntegerField()
    members = serializers.IntegerField()
    team = serializers.IntegerField()


class TemporalTimeSerializer(serializers.Serializer):
    lastYear = TemporalItemSerializer()
    last6Months = TemporalItemSerializer()
    last3Months = TemporalItemSerializer()
    lastMonth = TemporalItemSerializer()
    lastWeek = TemporalItemSerializer()
    last3Days = TemporalItemSerializer()
    today = TemporalItemSerializer()


class TemporalSerializer(serializers.Serializer):
    words = TemporalTimeSerializer()
    phrases = TemporalTimeSerializer()
    songs = TemporalTimeSerializer()
    stories = TemporalTimeSerializer()
    images = TemporalTimeSerializer()
    audio = TemporalTimeSerializer()
    video = TemporalTimeSerializer()


class SiteStatsSerializer(serializers.Serializer):
    aggregate = AggregateSerializer()
    temporal = TemporalSerializer()
