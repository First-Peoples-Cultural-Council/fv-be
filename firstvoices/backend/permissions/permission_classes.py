from rest_framework.permissions import BasePermission

from backend.permissions.predicates.view_models import can_view_team_content


class CanViewTeamContent(BasePermission):
    def has_permission(self, request, view):
        site = view.get_validated_site()
        return can_view_team_content(request.user, site)
