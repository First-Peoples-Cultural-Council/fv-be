from django.utils.translation import gettext as _

success_200_list = _(
    "Success. List may be empty if no resources are available for the current user."
)
success_200_detail = _("Success. Some field content may be hidden due to permissions.")
success_200_edit = _("Success. Updated resource in response.")

success_201 = _("Created. New resource in response.")

success_202_email = _("Success. Email sent.")
success_202_import_job_media = _("Success. Media added to the import-job.")
success_202_update_job_media = _("Success. Media added to the update-job.")
success_202_job_accepted = _("Job accepted.")

success_204_deleted = _("Success. Resource destroyed. No content in response.")

error_400_validation = _("Error. Invalid data.")

error_403 = _("Error. Not authorized.")
error_403_site_access_denied = _("Error. Not authorized for this site.")

error_404 = _("Error. Not found.")
error_404_missing_site = _("Error. Site not found.")
