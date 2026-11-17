from urllib.parse import quote, urlsplit

import requests
from django.conf import settings

from backend.views.exceptions import (
    MatomoConfigurationError,
    MatomoError,
    MatomoTimeoutError,
)


def get_monthly_visitors(site_slug, report_date):
    api_url = settings.MATOMO_API_URL
    token = settings.MATOMO_AUTH_TOKEN
    site_id = settings.MATOMO_SITE_ID
    tracked_site_url = settings.MATOMO_TRACKED_SITE_URL

    # Ensure all required Matomo configuration settings are present.
    if not api_url or not token or not site_id or not tracked_site_url:
        raise MatomoConfigurationError

    try:
        site_id = int(site_id)

        # Validate the Matomo API URL and tracked site URL to ensure they are properly configured.
        for configured_url in (api_url, tracked_site_url):
            parsed_url = urlsplit(configured_url)
            if (
                parsed_url.scheme != "https"
                or not parsed_url.hostname
                or parsed_url.username
                or parsed_url.password
                or parsed_url.query
                or parsed_url.fragment
            ):
                raise MatomoConfigurationError

        if site_id < 1 or urlsplit(tracked_site_url).path not in ("", "/"):
            raise MatomoConfigurationError
    except (TypeError, ValueError):
        raise MatomoConfigurationError from None

    # Construct the full site URL and encode it for use in the Matomo segment filter.
    site_url = f"{tracked_site_url.rstrip('/')}/{site_slug}"
    encoded_site_url = quote(site_url, safe="")
    encoded_subpage_url = quote(f"{site_url}/", safe="")
    segment = f"pageUrl=={encoded_site_url},pageUrl=^{encoded_subpage_url}"

    try:
        response = requests.post(
            api_url,
            data={
                "module": "API",
                "method": "VisitsSummary.get",
                "format": "JSON",
                "idSite": site_id,
                "period": "month",
                "date": report_date.isoformat(),
                "segment": segment,
                "token_auth": token,
            },
            timeout=(5, 15),
            allow_redirects=False,
        )
    except requests.Timeout:
        raise MatomoTimeoutError from None
    except requests.RequestException:
        raise MatomoError from None

    if response.status_code != 200:
        raise MatomoError

    try:
        report = response.json()
    except ValueError:
        raise MatomoError from None

    # Matomo can return an API error inside an HTTP 200 response.
    if not isinstance(report, dict) or report.get("result") == "error":
        raise MatomoError

    if "nb_visits" not in report and "nb_uniq_visitors" not in report:
        raise MatomoError

    # Missing metrics mean unavailable, but we need to preserve zero counts
    metrics = {}
    for metric_name, report_name in (
        ("total_visits", "nb_visits"),
        ("unique_visitors", "nb_uniq_visitors"),
    ):
        value = report.get(report_name)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise MatomoError
        metrics[metric_name] = value

    return metrics
