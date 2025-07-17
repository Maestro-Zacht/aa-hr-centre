from esi.clients import EsiClientProvider

from . import __version__ as app_version, __app_name_ua__ as app_name_ua, __github_url__ as github_url

esi = EsiClientProvider(
    ua_appname=app_name_ua,
    ua_version=app_version,
    ua_url=github_url,
)
