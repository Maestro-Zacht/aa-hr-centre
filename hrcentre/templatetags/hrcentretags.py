from django import template

from allianceauth.eveonline.models import EveCharacter

from securegroups.tasks import process_user

register = template.Library()


@register.filter
def ct_is_active(char: EveCharacter) -> bool:
    return char.characteraudit.is_active() if hasattr(char, 'characteraudit') else False


@register.filter
def hr_has_label(main, label):
    return getattr(main, f'has_label_{label.pk}', False)


@register.simple_tag
def sf_check(filter, user, bulk_data):
    return process_user(filter, user, bulk_data)


@register.filter
def sf_check_result(check, user):
    return check.result_for_user(user)
