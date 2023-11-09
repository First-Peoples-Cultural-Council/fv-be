from import_export import fields
from import_export.results import RowResult
from import_export.widgets import ForeignKeyWidget
from jwt_auth.models import User

from backend.models import Site
from backend.models.join_request import (
    JoinRequest,
    JoinRequestReason,
    JoinRequestReasonChoices,
    JoinRequestStatus,
)
from backend.resources.base import SiteContentResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class JoinRequestResource(SiteContentResource):
    user = fields.Field(
        column_name="user",
        attribute="user",
        widget=ForeignKeyWidget(User, "email"),
    )

    status = fields.Field(
        column_name="status",
        attribute="status",
        widget=ChoicesWidget(JoinRequestStatus.choices),
    )

    class Meta:
        model = JoinRequest

    def import_row(
        self,
        row,
        instance_loader,
        using_transactions=True,
        dry_run=False,
        raise_errors=None,
        **kwargs,
    ):
        # overriding import_row to ignore errors and skip rows that fail to import without failing the entire import
        # ref: https://github.com/django-import-export/django-import-export/issues/763
        import_result = super().import_row(row, instance_loader, **kwargs)
        skip_conditions = [User.DoesNotExist, Site.DoesNotExist]
        if (
            import_result.import_type == RowResult.IMPORT_TYPE_ERROR
            and type(import_result.errors[0].error) in skip_conditions
        ):
            # Copy the values to display in the preview report
            import_result.diff = [row[val] for val in row]
            # Add a column with the error message
            import_result.diff.append(
                f"Errors: {[err.error for err in import_result.errors]}"
            )
            # clear errors and mark the record to skip
            import_result.errors = []
            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        # add join request reasons
        if not row_result.import_type == RowResult.IMPORT_TYPE_SKIP:
            if (
                JoinRequest.objects.filter(id=row["id"]).exists()
                and row["reasons"] != ""
            ):
                join_request = JoinRequest.objects.get(id=row["id"])
                reasons = row["reasons"].strip().split(",")

                for reason in reasons:
                    reason = reason.strip('"').strip()
                    join_request_reason = JoinRequestReason.objects.create(
                        join_request=join_request,
                        reason=JoinRequestReasonChoices[reason].value,
                    )
                    join_request_reason.save()

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip join requests that already exist."""
        join_request_exists = JoinRequest.objects.filter(
            user=instance.user, site=instance.site
        ).exists()
        if join_request_exists:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)
