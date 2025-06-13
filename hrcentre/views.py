from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import F, Count, Subquery, OuterRef, Prefetch, Max, Min, Exists, Case, When
from django.db.models.lookups import LessThan
from django.db import transaction
from django.utils import timezone
from django.views.generic import View
from django.utils.functional import cached_property

from allianceauth.authentication.models import CharacterOwnership

from corptools.models import CharacterAudit

from .models import CorporationSetup, AllianceSetup, CharacterAuditLoginData, UserLabel, UserNotes, Label
from .forms import UserLabelsForm, UserNotesForm
from .utils import check_user_access, smartfilter_process_bulk


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
        object_list = self.main_qs()

        user_checks = self.get_checks()
        user_qs = User.objects.filter(pk__in=self.base_qs().values('character__character_ownership__user'))

        checks_dict = {ck: smartfilter_process_bulk(ck.filters.all(), user_qs) for ck in user_checks}

        labels = Label.objects.filter(
            pk__in=UserLabel.objects
            .filter(user__in=user_qs)
            .values('label')
        )

        for label in labels:
            object_list = object_list.annotate(
                **{
                    f'has_label_{label.pk}': Exists(
                        UserLabel.objects.filter(
                            user=OuterRef('character__character_ownership__user'),
                            label=label,
                        )
                    )
                }
            )

        context = {
            'group_name': self.get_object_name(),
            'mains': object_list,
            'checks': checks_dict,
            'labels': labels,
        }
        return render(request, self.template_name, context=context)

    def base_qs(self):
        raise NotImplementedError("Subclasses must implement base_queryset() method.")

    def get_object_name(self):
        raise NotImplementedError("Subclasses must implement get_object_name() method.")

    def get_checks(self):
        raise NotImplementedError("Subclasses must implement get_checks() method.")

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
                Prefetch(
                    'character__character_ownership__user__hr_labels',
                    queryset=UserLabel.objects.select_related('label'),
                )
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
                oldest_last_update=Case(
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

    @cached_property
    def model_object(self):
        return get_object_or_404(
            CorporationSetup.objects
            .select_related('corporation')
            .prefetch_related('checks__filters'),
            pk=self.kwargs['corp_id']
        )

    def get_object_name(self):
        return self.model_object.corporation.corporation_name

    def get_checks(self):
        return self.model_object.checks.all()

    def get(self, request, *args, **kwargs):
        corp_setup = self.model_object
        if not corp_setup.can_access(request.user):
            messages.error(request, _("You do not have permission to access this corporation setup."))
            return redirect('hrcentre:index')

        return super().get(request, *args, **kwargs)

    def base_qs(self):
        corp_setup = self.model_object
        return (
            CharacterAudit.objects
            .filter(
                character__character_ownership__user__profile__main_character=F('character'),
                character__corporation_id=corp_setup.corporation.corporation_id,
            )
        )


class AllianceAuditListView(CharacterAuditListView):

    @cached_property
    def model_object(self):
        return get_object_or_404(
            AllianceSetup.objects
            .select_related('alliance')
            .prefetch_related('checks__filters'),
            pk=self.kwargs['alliance_id']
        )

    def get_object_name(self):
        return self.model_object.alliance.alliance_name

    def get_checks(self):
        return self.model_object.checks.all()

    def get(self, request, *args, **kwargs):
        alliance_setup = self.model_object
        if not alliance_setup.can_access(request.user):
            messages.error(request, _("You do not have permission to access this alliance setup."))
            return redirect('hrcentre:index')

        return super().get(request, *args, **kwargs)

    def base_qs(self):
        alliance_setup = self.model_object
        return (
            CharacterAudit.objects
            .filter(
                character__character_ownership__user__profile__main_character=F('character'),
                character__alliance_id=alliance_setup.alliance.alliance_id,
            )
        )


@login_required
@permission_required('hrcentre.hr_access')
def user_view(request, user_id):
    main_char = get_object_or_404(
        CharacterAudit.objects
        .select_related(
            'character__character_ownership__user__hr_notes__added_by__profile__main_character',
            'character__character_ownership__user__hr_notes__last_updated_by__profile__main_character',
        )
        .filter(character__character_ownership__user__profile__main_character=F('character'))
        .annotate(
            number_of_chars=Count('character__character_ownership__user__character_ownerships'),
        ),
        character__character_ownership__user__id=user_id,
    )

    if not check_user_access(request.user, main_char):
        messages.error(request, _("You do not have permission to access this character."))
        return redirect('hrcentre:index')

    user_labels = (
        UserLabel.objects
        .filter(user=main_char.character.character_ownership.user)
        .select_related('label')
    )

    context = {
        'main': main_char,
        'labels': user_labels,
    }
    return render(request, 'hrcentre/user_view.html', context=context)


@login_required
@permission_required('hrcentre.hr_access')
def user_labels_view(request, user_id):
    main_char = get_object_or_404(
        CharacterAudit.objects
        .select_related('character__character_ownership__user')
        .filter(character__character_ownership__user__profile__main_character=F('character')),
        character__character_ownership__user__id=user_id,
    )

    if not check_user_access(request.user, main_char):
        messages.error(request, _("You do not have permission to access this character."))
        return redirect('hrcentre:index')

    user_labels = UserLabel.objects.filter(user=main_char.character.character_ownership.user).values_list('label', flat=True)

    if request.method == 'POST':
        form = UserLabelsForm(request.POST)
        if form.is_valid():
            selected_labels = form.cleaned_data['labels']

            with transaction.atomic():
                UserLabel.objects.filter(
                    user=main_char.character.character_ownership.user,
                ).exclude(
                    label__in=selected_labels,
                ).delete()

                for label in selected_labels:
                    UserLabel.objects.get_or_create(
                        user=main_char.character.character_ownership.user,
                        label=label,
                        defaults={'added_by': request.user},
                    )

            messages.success(request, _("Labels have been updated successfully."))
            return redirect('hrcentre:user_view', user_id=user_id)
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = UserLabelsForm(initial={'labels': user_labels})

    context = {
        'page_header': _("User Labels"),
        'form': form,
    }
    return render(request, 'hrcentre/generic_form.html', context=context)


@login_required
@permission_required('hrcentre.hr_access')
def user_notes_view(request, user_id):
    main_char = get_object_or_404(
        CharacterAudit.objects
        .select_related('character__character_ownership__user__hr_notes')
        .filter(character__character_ownership__user__profile__main_character=F('character')),
        character__character_ownership__user__id=user_id,
    )

    if not check_user_access(request.user, main_char):
        messages.error(request, _("You do not have permission to access this character."))
        return redirect('hrcentre:index')

    user_notes = UserNotes.objects.filter(user=main_char.character.character_ownership.user).first()

    if request.method == 'POST':
        form = UserNotesForm(request.POST, instance=user_notes)
        if form.is_valid():
            notes: UserNotes = form.save(commit=False)
            notes.user = main_char.character.character_ownership.user
            notes.last_updated_by = request.user
            if user_notes is None:
                notes.added_by = request.user
            notes.save()
            messages.success(request, _("Notes have been updated successfully."))
            return redirect('hrcentre:user_view', user_id)
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = UserNotesForm(instance=user_notes)

    context = {
        'page_header': _("User Notes"),
        'form': form,
    }
    return render(request, 'hrcentre/generic_form.html', context=context)
