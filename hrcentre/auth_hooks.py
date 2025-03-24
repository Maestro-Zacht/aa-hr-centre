from allianceauth import hooks
from allianceauth.services.hooks import UrlHook, MenuItemHook

from . import urls


class HRCentreMenuItemHook(MenuItemHook):
    def __init__(self):
        super().__init__("HR Centre", "fa-solid fa-users-rectangle", "hrcentre:index", navactive=["hrcentre:"])


@hooks.register('menu_item_hook')
def register_menu():
    return HRCentreMenuItemHook()


@hooks.register('url_hook')
def register_urls():
    return UrlHook(urls, 'hrcentre', 'hrcentre/')
