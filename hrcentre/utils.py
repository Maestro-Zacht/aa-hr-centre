from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404

from corptools.models import CharacterAudit

from .models import AllianceSetup, CorporationSetup, LabelGrouping, UserLabel


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


@transaction.atomic
def save_labels(user: User, form_data: dict, request_user: User):
    for grouping_name, labels in form_data.items():
        grouping = get_object_or_404(LabelGrouping, name=grouping_name)

        if grouping.multiple_selection:
            UserLabel.objects.filter(
                user=user,
                label__grouping=grouping,
            ).exclude(
                label__in=labels
            ).delete()

            for label in labels:
                UserLabel.objects.get_or_create(
                    user=user,
                    label=label,
                    defaults={'added_by': request_user}
                )
        else:
            label = labels.first() if grouping.options.count() == 1 else labels
            UserLabel.objects.filter(
                user=user,
                label__grouping=grouping,
            ).exclude(
                label=label
            ).delete()

            if label:
                UserLabel.objects.get_or_create(
                    user=user,
                    label=label,
                    defaults={'added_by': request_user}
                )
