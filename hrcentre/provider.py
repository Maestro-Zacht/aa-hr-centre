from esi.clients import EsiClientProvider

from esi import __version__ as esi_version

from . import __version__ as hrcentre_version

APP_NAME = "aa-hr-centre"
GITHUB_URL = "https://github.com/Maestro-Zacht/aa-hr-centre"

esi = EsiClientProvider(
    app_info_text=f"{APP_NAME}/{hrcentre_version} (+{GITHUB_URL}) Django-ESI/{esi_version}"
)
