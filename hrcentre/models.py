from django.db import models
from django.contrib.auth.models import Group, User
from django.utils.translation import gettext_lazy as _

from allianceauth.eveonline.models import EveCorporationInfo, EveAllianceInfo

from securegroups.models import SmartFilter


class General(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('hr_access', 'Can access HR Centre'),
        )


class UsersCheck(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')

    filters = models.ManyToManyField(SmartFilter, related_name='+')

    class OperatorChoices(models.TextChoices):
        AND = "and"
        OR = "or"
        XOR = "xor"

    operator = models.CharField(
        max_length=10,
        choices=OperatorChoices.choices,
        default=OperatorChoices.AND
    )
    negate = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name

    def with_parsed_filters(self, users):
        if not hasattr(self, 'hr_bulk_checks'):
            self.hr_bulk_checks = {}
            for f in self.filters.all():
                try:
                    self.hr_bulk_checks[f.id] = f.filter_object.audit_filter(users)
                except Exception:
                    pass
        return self

    def result_for_user(self, user):
        if not hasattr(self, 'hr_bulk_checks'):
            raise ValueError("Checks have not been processed.")

        filter_results = [self.hr_bulk_checks[f.id][user.id]['check'] for f in self.filters.all()]

        if self.operator == self.OperatorChoices.AND:
            result = all(filter_results)
        elif self.operator == self.OperatorChoices.OR:
            result = any(filter_results)
        elif self.operator == self.OperatorChoices.XOR:
            result = filter_results.count(True) == 1
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

        if self.negate:
            result = not result
        return result


class Setup(models.Model):
    access_list = models.ManyToManyField(
        Group,
        blank=True,
        related_name='+'
    )

    checks = models.ManyToManyField(UsersCheck, blank=True)

    class Meta:
        abstract = True
        default_permissions = ()

    def can_access(self, user: User) -> bool:
        if user.is_superuser:
            return True
        return user.groups.filter(id__in=self.access_list.all()).exists()

    @classmethod
    def get_setup_list(cls, user: User):
        if user.is_superuser:
            return cls.objects.all()
        return cls.objects.filter(access_list__in=user.groups.all()).distinct()


class AllianceSetup(Setup):
    alliance = models.OneToOneField(
        EveAllianceInfo,
        on_delete=models.RESTRICT,
        primary_key=True,
        related_name='hrcentre_setup'
    )

    class Meta:
        default_permissions = ()

    def __str__(self):
        return f'HR setup - {self.alliance}'


class CorporationSetup(Setup):
    corporation = models.OneToOneField(
        EveCorporationInfo,
        on_delete=models.RESTRICT,
        primary_key=True,
        related_name='hrcentre_setup'
    )

    class Meta:
        default_permissions = ()

    def __str__(self):
        return f'HR setup - {self.corporation}'


class LabelGrouping(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, default='')

    can_self_assign = models.BooleanField(default=False)

    multiple_selection = models.BooleanField(default=False)
    allow_empty = models.BooleanField(default=True)

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name

    @property
    def form_help_text(self):
        if not self.allow_empty and self.multiple_selection:
            return _('Select at least one option.')
        elif not self.allow_empty:
            return _('Select an option.')


class Label(models.Model):
    name = models.CharField(max_length=64, unique=True)

    grouping = models.ForeignKey(LabelGrouping, on_delete=models.CASCADE, related_name='options')

    class LabelColorOptions(models.TextChoices):
        BLUE = 'blue'
        RED = 'red'
        GREEN = 'green'
        YELLOW = 'yellow'

    color = models.CharField(
        max_length=16,
        choices=LabelColorOptions.choices,
        default=LabelColorOptions.BLUE
    )

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name

    @property
    def bs_class(self):
        if self.color == Label.LabelColorOptions.RED:
            return 'text-bg-danger'
        elif self.color == Label.LabelColorOptions.GREEN:
            return 'text-bg-success'
        elif self.color == Label.LabelColorOptions.BLUE:
            return 'text-bg-primary'
        elif self.color == Label.LabelColorOptions.YELLOW:
            return 'text-bg-warning'
        return 'text-bg-secondary'

    @property
    def form_bs_class(self):
        if self.color == Label.LabelColorOptions.RED:
            return 'btn-outline-danger'
        elif self.color == Label.LabelColorOptions.GREEN:
            return 'btn-outline-success'
        elif self.color == Label.LabelColorOptions.BLUE:
            return 'btn-outline-primary'
        elif self.color == Label.LabelColorOptions.YELLOW:
            return 'btn-outline-warning'
        return 'btn-outline-secondary'


class UserLabel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hr_labels'
    )
    label = models.ForeignKey(
        Label,
        on_delete=models.CASCADE,
        related_name='user_labels'
    )

    added_by = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='+'
    )
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'label'],
                name='unique_user_label'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.label}'


class UserNotes(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='hr_notes',
        primary_key=True,
    )
    notes = models.TextField(blank=True, default='')

    added_by = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='+',
    )
    added_on = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='+',
    )
    last_updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return str(self.user)
