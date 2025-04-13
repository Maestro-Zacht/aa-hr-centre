from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import F, Count, Subquery, OuterRef, Prefetch, Max, Min, Exists, Case, When
from django.db.models.lookups import LessThan
from django.utils import timezone
from django.views.generic import View

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


class CharacterAuditListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'hrcentre/group_view.html'
    permission_required = "hrcentre.hr_access"

    def get(self, request, *args, **kwargs):
        self.object_list = self.main_qs()
        context = {
            'group_name': "test",
            'mains': self.object_list,
        }
        return render(request, self.template_name, context=context)

    def base_qs(self):
        raise NotImplementedError("Subclasses must implement base_queryset() method.")

    def main_qs(self):
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

        return (
            self.base_qs()
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


class CorporationAuditListView(CharacterAuditListView):
    def get(self, request, *args, **kwargs):
        corp_setup = get_object_or_404(
            CorporationSetup.objects.select_related('corporation'),
            pk=self.kwargs['corp_id']
        )
        if not corp_setup.can_access(request.user):
            messages.error(request, _("You do not have permission to access this corporation setup."))
            return redirect('hrcentre:index')

        return super().get(request, *args, **kwargs)

    def base_qs(self):
        corp_setup = get_object_or_404(
            CorporationSetup.objects.select_related('corporation'),
            pk=self.kwargs['corp_id']
        )
        return (
            CharacterAudit.objects
            .filter(
                character__character_ownership__user__profile__main_character=F('character'),
                character__corporation_id=corp_setup.corporation.corporation_id,
            )
        )


class AllianceAuditListView(CharacterAuditListView):
    def get(self, request, *args, **kwargs):
        alliance_setup = get_object_or_404(
            AllianceSetup.objects.select_related('alliance'),
            pk=self.kwargs['alliance_id']
        )
        if not alliance_setup.can_access(request.user):
            messages.error(request, _("You do not have permission to access this alliance setup."))
            return redirect('hrcentre:index')

        return super().get(request, *args, **kwargs)

    def base_qs(self):
        alliance_setup = get_object_or_404(
            AllianceSetup.objects.select_related('alliance'),
            pk=self.kwargs['alliance_id']
        )
        return (
            CharacterAudit.objects
            .filter(
                character__character_ownership__user__profile__main_character=F('character'),
                character__alliance_id=alliance_setup.alliance.alliance_id,
            )
        )
