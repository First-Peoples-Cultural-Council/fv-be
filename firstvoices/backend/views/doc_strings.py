from django.utils.translation import gettext as _

success_list_200 = _(
    "Success. List may be empty if no resources are available for the current user."
)
success_item_200 = _("Success. Some field content may be hidden due to permissions.")
success_201 = _("Created. New resource in response.")

error_validation_400 = _("Error. Invalid request.")
error_403 = _("Error. Not authorized.")
error_404 = _("Error. Not found.")

site_content_list_error_403 = _("Error. Not authorized for this site.")
site_content_list_error_404 = _("Error. Site not found.")
