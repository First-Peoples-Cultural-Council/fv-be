from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from backend.models import Character, DictionaryEntry, Gallery, Song, Story
from backend.permissions.utils import filter_by_viewable
from backend.serializers.base_serializers import (
    LinkedSiteSerializer,
    SiteContentLinkedTitleSerializer,
)
from backend.serializers.media_serializers import (
    AudioSerializer,
    ImageSerializer,
    VideoSerializer,
)
from backend.serializers.page_serializers import SitePageUsageSerializer
from backend.serializers.utils import get_usages_total


class GenericUsageSerializer(
    SiteContentLinkedTitleSerializer, NestedHyperlinkedModelSerializer
):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = None


def usage_related_set(self, model, related_set, many=True):
    GenericUsageSerializer.Meta.model = model
    if self.context["request"].user:
        user = self.context["request"].user
        related_set = filter_by_viewable(user, related_set)
    return GenericUsageSerializer(related_set, many=many, context=self.context).data


class BaseUsageFieldSerializer(serializers.ModelSerializer):
    usage = serializers.SerializerMethodField()

    class Meta:
        fields = ("usage",)

    def get_usage(self, obj):
        characters = usage_related_set(self, Character, obj.character_set.all())
        dictionary_entries = usage_related_set(
            self, DictionaryEntry, obj.dictionaryentry_set.all()
        )
        songs = usage_related_set(self, Song, obj.song_set.all())

        # Returning only stories and not pages, whether the media is on the cover or in any page
        parent_stories_ids = obj.storypage_set.values_list("story", flat=True)
        parent_stories_qs = Story.objects.filter(id__in=parent_stories_ids)
        parent_stories = usage_related_set(self, Story, parent_stories_qs)

        story_covers = usage_related_set(self, Story, obj.story_set.all())
        # Returning only unique values
        stories = list(
            {story["id"]: story for story in (parent_stories + story_covers)}.values()
        )

        response_dict = {
            "characters": characters,
            "dictionary_entries": dictionary_entries,
            "songs": songs,
            "stories": stories,
        }

        response_dict["total"] = get_usages_total(response_dict)

        return response_dict


class VisualMediaUsageFieldSerializer(BaseUsageFieldSerializer):
    def get_usage(self, obj):
        response_dict = BaseUsageFieldSerializer.get_usage(self, obj)

        site_page_qs = obj.sitepage_set.all()

        if self.context["request"].user:
            user = self.context["request"].user
            site_page_qs = filter_by_viewable(user, site_page_qs)

        site_pages = SitePageUsageSerializer(
            site_page_qs, context=self.context, many=True
        ).data

        response_dict = {
            **response_dict,
            "custom_pages": site_pages,
        }

        response_dict["total"] = get_usages_total(response_dict)
        return response_dict


class AudioDetailSerializer(BaseUsageFieldSerializer, AudioSerializer):
    class Meta(AudioSerializer.Meta):
        fields = AudioSerializer.Meta.fields + BaseUsageFieldSerializer.Meta.fields


class VideoDetailSerializer(VisualMediaUsageFieldSerializer, VideoSerializer):
    class Meta(VideoSerializer.Meta):
        fields = (
            VideoSerializer.Meta.fields + VisualMediaUsageFieldSerializer.Meta.fields
        )


class ImageDetailSerializer(VisualMediaUsageFieldSerializer, ImageSerializer):
    class Meta(ImageSerializer.Meta):
        fields = (
            ImageSerializer.Meta.fields + VisualMediaUsageFieldSerializer.Meta.fields
        )

    def get_usage(self, obj):
        response_dict = VisualMediaUsageFieldSerializer.get_usage(self, obj)
        gallery_cover_image_of = usage_related_set(
            self, Gallery, obj.gallery_cover_image.all()
        )

        site_banner_of = {}
        if hasattr(obj, "site_banner_of"):
            site_banner_of = LinkedSiteSerializer(
                obj.site_banner_of, context=self.context
            ).data

        site_logo_of = {}
        if hasattr(obj, "site_logo_of"):
            site_logo_of = LinkedSiteSerializer(
                obj.site_logo_of, context=self.context
            ).data

        gallery_images = []
        for gallery_item in obj.gallery_images.all():
            gallery_images.append(
                usage_related_set(self, Gallery, gallery_item.gallery, many=False)
            )

        # returning only unique values
        gallery = list(
            {
                gallery["id"]: gallery
                for gallery in (gallery_cover_image_of + gallery_images)
            }.values()
        )

        response_dict = {
            **response_dict,
            "gallery": gallery,
            "site_banner": site_banner_of,
            "site_logo": site_logo_of,
        }

        response_dict["total"] = get_usages_total(response_dict)
        return response_dict
