from backend.models.constants import Visibility
from backend.models.sites import Language, Site
from backend.search.documents.language_document import LanguageDocument
from backend.search.indexing.base import DocumentManager, IndexManager
from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from backend.search.utils.get_index_documents import _fields_as_list, _text_as_list


class LanguageDocumentManager(DocumentManager):
    index = ELASTICSEARCH_LANGUAGE_INDEX
    document = LanguageDocument
    model = Language

    @classmethod
    def create_index_document(cls, instance: Language):
        """Returns a LanguageDocument populated for the given Language instance."""
        visible_sites = (
            instance.sites.all()
            .filter(visibility__gte=Visibility.MEMBERS)
            .filter(is_hidden=False)
        )

        return cls.document(
            document_id=str(instance.id),
            document_type=instance.__class__.__name__,
            language_name=instance.title,
            sort_title=instance.title.upper(),
            language_code=_text_as_list(instance.language_code),
            language_alternate_names=_text_as_list(instance.alternate_names),
            language_community_keywords=_text_as_list(instance.community_keywords),
            site_names=_fields_as_list(visible_sites, "title"),
            site_slugs=_fields_as_list(visible_sites, "slug"),
            language_family_name=instance.language_family.title,
            language_family_alternate_names=_text_as_list(
                instance.language_family.alternate_names
            ),
        )

    @classmethod
    def should_be_indexed(cls, instance):
        """
        Conditions for indexing a Language:
         * has at least one non-hidden Site with visibility of Members or Public
        """
        visible_sites = instance.sites.filter(
            visibility__gte=Visibility.MEMBERS
        ).filter(is_hidden=False)
        return visible_sites.exists()


class SiteDocumentManager(DocumentManager):
    index = ELASTICSEARCH_LANGUAGE_INDEX
    document = LanguageDocument
    model = Site

    @classmethod
    def create_index_document(cls, instance: Site):
        """Returns a LanguageDocument populated for the given Site instance, with the assumption that the Site has
        no associated Language."""
        return cls.document(
            document_id=str(instance.id),
            document_type=instance.__class__.__name__,
            sort_title=instance.title.upper(),
            language_name=None,
            language_code=None,
            language_alternate_names=None,
            language_community_keywords=None,
            site_names=instance.title,
            site_slugs=instance.slug,
            language_family_name=None,
            language_family_alternate_names=None,
        )

    @classmethod
    def should_be_indexed(cls, instance: Site):
        """
        Conditions for indexing a Site:
         * has no Language assigned
         * has visibility of Members or Public
         * is not hidden
        """

        return (
            instance.language is None
            and instance.visibility >= Visibility.MEMBERS
            and not instance.is_hidden
        )


class LanguageIndexManager(IndexManager):
    index = ELASTICSEARCH_LANGUAGE_INDEX
    document_managers = [LanguageDocumentManager, SiteDocumentManager]
