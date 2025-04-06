from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import F, Count, Subquery, OuterRef, Prefetch, Max, Min, Exists, Case, When
from django.db.models.lookups import LessThan
from django.utils import timezone

from allianceauth.authentication.models import CharacterOwnership

from corptools.models import CharacterAudit

from .models import CorporationSetup, AllianceSetup, CharacterAuditLoginData


@login_required
@permission_required('hrcentre.hr_access')
def index(request):
    corps = CorporationSetup.get_setup_list(request.user).select_related('corporation')
    alliances = AllianceSetup.get_setup_list(request.user).select_related('alliance')

    context = {
        'corp_setups': corps,
        'alliance_setups': alliances,
    }
    return render(request, 'hrcentre/index.html', context=context)


@login_required
@permission_required('hrcentre.hr_access')
def corp_view(request, corp_id):
    corp_setup = get_object_or_404(
        CorporationSetup.objects.select_related('corporation'),
        pk=corp_id
    )

    if not corp_setup.can_access(request.user):
        messages.error(request, _("You do not have permission to access this corporation setup."))
        return redirect('hrcentre:index')

    ownership_qs = (
        CharacterOwnership.objects
        .select_related('character__characteraudit')
        .annotate(
            last_login=Subquery(
                CharacterAuditLoginData.objects
                .filter(characteraudit__character=OuterRef('character'))
                .values('last_login')
            )
        )
    )
    user_login_qs = (
        CharacterAuditLoginData.objects
        .filter(
            characteraudit__character__character_ownership__user=OuterRef('character__character_ownership__user')
        )
        .values('characteraudit__character__character_ownership__user')
    )

    mains = (
        CharacterAudit.objects
        .filter(
            character__character_ownership__user__profile__main_character=F('character'),
            character__corporation_id=corp_setup.corporation.corporation_id,
        )
        .select_related('character__character_ownership__user')
        .prefetch_related(
            Prefetch(
                'character__character_ownership__user__character_ownerships',
                queryset=ownership_qs,
                to_attr='chars',
            ),
        )
        .annotate(
            last_login=Subquery(
                user_login_qs
                .annotate(last_login=Max('last_login'))
                .values('last_login')
            )
        )
        .annotate(
            is_updating=Case(
                When(
                    LessThan(
                        Subquery(
                            user_login_qs
                            .annotate(last_update=Min('last_update'))
                            .values('last_update')
                        ),
                        timezone.now() - timezone.timedelta(days=1),
                    ) |
                    Exists(
                        CharacterAuditLoginData.objects
                        .filter(
                            characteraudit__character__character_ownership__user=OuterRef('character__character_ownership__user'),
                            last_update__isnull=True
                        )
                    ) |
                    Exists(
                        CharacterOwnership.objects
                        .filter(
                            character__characteraudit__isnull=True,
                            user=OuterRef('character__character_ownership__user'),
                        )
                    ),
                    then=False
                ),
                default=True,
            )
        )
        .annotate(
            older_last_update=Case(
                When(
                    Exists(
                        CharacterAuditLoginData.objects
                        .filter(
                            characteraudit__character__character_ownership__user=OuterRef('character__character_ownership__user'),
                            last_update__isnull=True
                        )
                    ) |
                    Exists(
                        CharacterOwnership.objects
                        .filter(
                            character__characteraudit__isnull=True,
                            user=OuterRef('character__character_ownership__user'),
                        )
                    ),
                    then=None
                ),
                default=Subquery(
                    user_login_qs
                    .annotate(last_update=Min('last_update'))
                    .values('last_update')
                )
            )
        )
        .annotate(
            number_of_chars=Count('character__character_ownership__user__character_ownerships'),
        )
    )

    context = {
        'group_name': corp_setup.corporation.corporation_name,
        'mains': mains,
    }

    return render(request, 'hrcentre/group_view.html', context=context)


@login_required
@permission_required('hrcentre.hr_access')
def alliance_view(request, alliance_id):
    alliance_setup = get_object_or_404(
        AllianceSetup.objects.select_related('alliance'),
        pk=alliance_id
    )

    if not alliance_setup.can_access(request.user):
        messages.error(request, _("You do not have permission to access this alliance setup."))
        return redirect('hrcentre:index')

    ownership_qs = (
        CharacterOwnership.objects
        .select_related('character__characteraudit')
        .annotate(
            last_login=Subquery(
                CharacterAuditLoginData.objects
                .filter(characteraudit__character=OuterRef('character'))
                .values('last_login')
            )
        )
    )
    user_login_qs = (
        CharacterAuditLoginData.objects
        .filter(
            characteraudit__character__character_ownership__user=OuterRef('character__character_ownership__user')
        )
        .values('characteraudit__character__character_ownership__user')
    )

    mains = (
        CharacterAudit.objects
        .filter(
            character__character_ownership__user__profile__main_character=F('character'),
            character__alliance_id=alliance_setup.alliance.alliance_id,
        )
        .select_related('character__character_ownership__user')
        .prefetch_related(
            Prefetch(
                'character__character_ownership__user__character_ownerships',
                queryset=ownership_qs,
                to_attr='chars',
            ),
        )
        .annotate(
            last_login=Subquery(
                user_login_qs
                .annotate(last_login=Max('last_login'))
                .values('last_login')
            )
        )
        .annotate(
            is_updating=Case(
                When(
                    LessThan(
                        Subquery(
                            user_login_qs
                            .annotate(last_update=Min('last_update'))
                            .values('last_update')
                        ),
                        timezone.now() - timezone.timedelta(days=1),
                    ) |
                    Exists(
                        CharacterAuditLoginData.objects
                        .filter(
                            characteraudit__character__character_ownership__user=OuterRef('character__character_ownership__user'),
                            last_update__isnull=True
                        )
                    ) |
                    Exists(
                        CharacterOwnership.objects
                        .filter(
                            character__characteraudit__isnull=True,
                            user=OuterRef('character__character_ownership__user'),
                        )
                    ),
                    then=False
                ),
                default=True,
            )
        )
        .annotate(
            older_last_update=Case(
                When(
                    Exists(
                        CharacterAuditLoginData.objects
                        .filter(
                            characteraudit__character__character_ownership__user=OuterRef('character__character_ownership__user'),
                            last_update__isnull=True
                        )
                    ) |
                    Exists(
                        CharacterOwnership.objects
                        .filter(
                            character__characteraudit__isnull=True,
                            user=OuterRef('character__character_ownership__user'),
                        )
                    ),
                    then=None
                ),
                default=Subquery(
                    user_login_qs
                    .annotate(last_update=Min('last_update'))
                    .values('last_update')
                )
            )
        )
        .annotate(
            number_of_chars=Count('character__character_ownership__user__character_ownerships'),
        )
    )

    context = {
        'group_name': alliance_setup.alliance.alliance_name,
        'mains': mains,
    }

    return render(request, 'hrcentre/group_view.html', context=context)
