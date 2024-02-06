from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from backend.models import Character, DictionaryEntry, Gallery, SitePage, Song, Story
from backend.serializers.base_serializers import (
    LinkedSiteSerializer,
    SiteContentLinkedTitleSerializer,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import (
    AudioSerializer,
    ImageSerializer,
    VideoSerializer,
)


def usage_related_set(self, model, related_set, many=True):
    GenericUsageSerializer.Meta.model = model
    return GenericUsageSerializer(related_set, many=many, context=self.context).data


def get_usages_total(usages_dict):
    # Get total count of all objects a media file is used in
    total = 0
    for usage in usages_dict.values():
        if isinstance(
            usage, list
        ):  # adding a check as some keys contain objects and not arrays
            total += len(usage)
        else:
            total += 1
    return total


class GenericUsageSerializer(
    SiteContentLinkedTitleSerializer, NestedHyperlinkedModelSerializer
):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = None


class SitePageUsageSerializer(serializers.ModelSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitepage-detail", lookup_field="slug", read_only=True
    )

    class Meta:
        model = SitePage
        fields = (
            "id",
            "url",
            "title",
        )


class BaseUsageFieldMixin(serializers.ModelSerializer):
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
        parent_stories = []
        for story_page in obj.storypage_set.all():
            parent_stories.append(
                usage_related_set(self, Story, story_page.story, many=False)
            )
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


class VisualMediaUsageFieldMixin(BaseUsageFieldMixin):
    def get_usage(self, obj):
        response_dict = BaseUsageFieldMixin.get_usage(
            self, obj
        )  # Can we do super() here ?

        site_pages = SitePageUsageSerializer(
            obj.sitepage_set.all(), context=self.context, many=True
        ).data

        response_dict = {
            **response_dict,
            "custom_pages": site_pages,
        }

        del response_dict["total"]
        response_dict["total"] = get_usages_total(response_dict)
        return response_dict


class AudioDetailSerializer(BaseUsageFieldMixin, AudioSerializer):
    class Meta(AudioSerializer.Meta):
        fields = AudioSerializer.Meta.fields + BaseUsageFieldMixin.Meta.fields


class VideoDetailSerializer(VisualMediaUsageFieldMixin, VideoSerializer):
    class Meta(VideoSerializer.Meta):
        fields = VideoSerializer.Meta.fields + VisualMediaUsageFieldMixin.Meta.fields


class ImageDetailSerializer(VisualMediaUsageFieldMixin, ImageSerializer):
    class Meta(ImageSerializer.Meta):
        fields = ImageSerializer.Meta.fields + VisualMediaUsageFieldMixin.Meta.fields

    def get_usage(self, obj):
        response_dict = VisualMediaUsageFieldMixin.get_usage(self, obj)
        gallery_cover_image_of = usage_related_set(
            self, Gallery, obj.gallery_cover_image.all()
        )
        site_banner_of = LinkedSiteSerializer(
            obj.site_banner_of, context=self.context
        ).data
        site_logo_of = LinkedSiteSerializer(obj.site_logo_of, context=self.context).data

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

        del response_dict["total"]
        response_dict["total"] = get_usages_total(response_dict)
        return response_dict
