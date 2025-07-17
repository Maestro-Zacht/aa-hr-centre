from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.services.hooks import UrlHook, MenuItemHook

from . import urls
from .views import dashboard_labels


class HRCentreMenuItemHook(MenuItemHook):
    def __init__(self):
        super().__init__(_("HR Centre"), "fa-solid fa-users-rectangle", "hrcentre:index", navactive=["hrcentre:"])

    def render(self, request):
        if request.user.has_perm('hrcentre.hr_access'):
            return super().render(request)
        return ''


class DashboardLabelsHook(hooks.DashboardItemHook):
    def __init__(self):
        super().__init__(
            dashboard_labels,
            7,
        )


@hooks.register('menu_item_hook')
def register_menu():
    return HRCentreMenuItemHook()


@hooks.register('url_hook')
def register_urls():
    return UrlHook(urls, 'hrcentre', 'hrcentre/')


@hooks.register('dashboard_hook')
def register_login_hook():
    return DashboardLabelsHook()
