from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from backend.models import Alphabet, Character, CharacterVariant, IgnoredCharacter, Site
from backend.models.jobs import JobStatus
from backend.permissions import utils
from backend.views.utils import BurstRateThrottle, SustainedRateThrottle


class ThrottlingMixin:
    """
    A mixin to provide request usage throttling for viewsets.
    """

    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]


class FVPermissionViewSetMixin(ThrottlingMixin):
    """
    Forked from ``rules.contrib.rest_framework.AutoPermissionViewSetMixin`` to provide extension points.

    Enforces object-level permissions in ``rest_framework.viewsets.ViewSet``,
    deriving the permission type from the particular action to be performed. List results are
    filtered to only include permitted items.

    As with ``rules.contrib.views.AutoPermissionRequiredMixin``, this only works when
    model permissions are registered using ``rules.contrib.models.RulesModelMixin``.

    Override ``get_object_for_create_permission`` to check 'create' permissions
    on an object if desired (defaults to a None object).
    """

    # Maps API actions to model permission types. None as value skips permission
    # checks for the particular action.
    # This map needs to be extended when custom actions are implemented
    # using the @action decorator.
    # Extend or replace it in subclasses like so:
    # permission_type_map = {
    #     **AutoPermissionViewSetMixin.permission_type_map,
    #     "close": "change",
    #     "reopen": "change",
    # }
    permission_type_map = {
        "create": "add",
        "destroy": "delete",
        "list": None,
        "partial_update": "change",
        "retrieve": "view",
        "update": "change",
    }

    def initial(self, *args, **kwargs):
        """Ensures user has permission to perform the requested action."""
        super().initial(*args, **kwargs)

        if not self.request.user:
            # No user, don't check permission
            return

        # Get the handler for the HTTP method in use
        try:
            if self.request.method.lower() not in self.http_method_names:
                raise AttributeError
            handler = getattr(self, self.request.method.lower())
        except AttributeError:
            # method not supported, will be denied anyway
            return

        try:
            perm_type = self.permission_type_map[self.action]
        except KeyError:
            raise ImproperlyConfigured(
                "FVPermissionViewSetMixin tried to authorize a request with the "
                "{!r} action, but permission_type_map only contains: {!r}".format(
                    self.action, self.permission_type_map
                )
            )
        if perm_type is None:
            # Skip permission checking for this action
            return

        # Determine whether we've to check object permissions (for detail actions)
        obj = None
        extra_actions = self.get_extra_actions()
        # We have to access the unbound function via __func__
        if handler.__func__ in extra_actions:
            if handler.detail:
                obj = self.get_object()
        elif self.action == "create":
            obj = self.get_object_for_create_permission()
        elif self.action not in ("create", "list"):
            obj = self.get_object()

        # Finally, check permission
        perm = self.get_queryset().model.get_perm(perm_type)
        if not self.request.user.has_perm(perm, obj):
            raise PermissionDenied

    def get_object_for_create_permission(self):
        """Subclasses can override to return an object to be used for checking create permissions"""
        return None

    def get_queryset(self):
        """
        Allows implementing different querysets for list and detail
        """
        if self.action == "list":
            return self.get_list_queryset()
        else:
            return self.get_detail_queryset()

    def get_list_queryset(self):
        """Defaults to basic get_queryset behaviour"""
        return super().get_queryset()

    def get_detail_queryset(self):
        """Defaults to basic get_queryset behaviour"""
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        # permissions
        queryset = utils.filter_by_viewable(request.user, self.get_queryset())

        # pagination
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data)


class SiteContentViewSetMixin:
    """
    Provides common methods for handling site content, usually for data models that use the ``BaseSiteContentModel``.
    """

    def get_site_slug(self):
        return self.kwargs["site_slug"]

    def get_serializer_context(self):
        """
        Add the site to the extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        context["site"] = self.get_validated_site()
        return context

    def get_validated_site(self):
        site_slug = self.get_site_slug()
        sites = Site.objects.filter(slug=site_slug)

        if not sites.exists():
            raise Http404

        site = sites.first()

        # Check permissions on the site first
        perm = Site.get_perm("view")
        if self.request.user.has_perm(perm, site):
            return site
        else:
            raise PermissionDenied

    def get_object_for_create_permission(self):
        """Check create permissions based on the relevant site"""
        return self.get_validated_site()


class DictionarySerializerContextMixin:
    """
    Adds context to a view which is passed to the dictionary serializer to remove the need for duplicate queries.
    """

    def get_serializer_context(self):
        """
        A helper function to gather additional model context which can be reused for multiple dictionary entries.
        """

        site = self.get_validated_site()

        context = super().get_serializer_context()

        alphabet = Alphabet.objects.get_or_create(site=site)[0]
        ignored_characters = IgnoredCharacter.objects.filter(site=site).values_list(
            "title", flat=True
        )
        base_characters = Character.objects.filter(site=site).order_by("sort_order")
        character_variants = CharacterVariant.objects.filter(site=site)
        ignorable_characters = IgnoredCharacter.objects.filter(site=site)

        context["alphabet"] = alphabet
        context["ignored_characters"] = ignored_characters
        context["base_characters"] = base_characters
        context["character_variants"] = character_variants
        context["ignorable_characters"] = ignorable_characters
        return context


class AsyncJobDeleteMixin:
    """Blocks job instances from being deleted after they have started running."""

    started_statuses = [JobStatus.STARTED, JobStatus.COMPLETE]

    def perform_destroy(self, instance):
        if instance.status in self.started_statuses:
            raise ValidationError(
                f"Can't delete a job after it has been started. This job already has status {instance.status}"
            )

        super().perform_destroy(instance)
