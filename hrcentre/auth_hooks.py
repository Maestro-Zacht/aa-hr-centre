from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.services.hooks import UrlHook, MenuItemHook

from . import urls


class HRCentreMenuItemHook(MenuItemHook):
    def __init__(self):
        super().__init__(_("HR Centre"), "fa-solid fa-users-rectangle", "hrcentre:index", navactive=["hrcentre:"])

    def render(self, request):
        if request.user.has_perm('hrcentre.hr_access'):
            return super().render(request)
        return ''


@hooks.register('menu_item_hook')
def register_menu():
    return HRCentreMenuItemHook()


@hooks.register('url_hook')
def register_urls():
    return UrlHook(urls, 'hrcentre', 'hrcentre/')
