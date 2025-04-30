from django.contrib.auth.models import User

from corptools.models import CharacterAudit

from securegroups.models import SmartFilter

from .models import AllianceSetup, CorporationSetup


def check_user_access(user: User, main: CharacterAudit) -> bool:
    try:
        corp_setup = CorporationSetup.objects.get(corporation__corporation_id=main.character.corporation_id)
    except CorporationSetup.DoesNotExist:
        corp_setup = None

    try:
        alliance_setup = AllianceSetup.objects.get(alliance__alliance_id=main.character.alliance_id)
    except AllianceSetup.DoesNotExist:
        alliance_setup = None

    can_access = False
    if corp_setup:
        can_access = corp_setup.can_access(user)
    if not can_access and alliance_setup:
        can_access = alliance_setup.can_access(user)
    return can_access


def smartfilter_process_bulk(filters, users):
    bulk_checks = {}
    for f in filters:
        try:
            bulk_checks[f.id] = f.filter_object.audit_filter(users)
        except Exception:
            pass
    return bulk_checks
