from django.db import models
from django.contrib.auth.models import Group, User

from allianceauth.eveonline.models import EveCorporationInfo, EveAllianceInfo

from corptools.models import CharacterAudit

from securegroups.models import SmartFilter


class General(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('hr_access', 'Can access HR Centre'),
        )


class Setup(models.Model):
    access_list = models.ManyToManyField(
        Group,
        blank=True,
        related_name='+'
    )

    checks = models.ManyToManyField('UsersCheck')

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


class CharacterAuditLoginData(models.Model):
    characteraudit = models.OneToOneField(
        CharacterAudit,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='login_data'
    )
    last_login = models.DateTimeField(null=True, blank=True)
    last_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        default_permissions = ()


class Label(models.Model):
    name = models.CharField(max_length=64, unique=True)

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


class UserLabel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hr_labels'
    )
    label = models.ForeignKey(
        Label,
        on_delete=models.CASCADE,
        related_name='+'
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


class UsersCheck(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')

    filters = models.ManyToManyField(SmartFilter, related_name='+')

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name


class LabelGrouping(models.Model):
    options = models.ManyToManyField(Label, related_name='+')
    multiple_selection = models.BooleanField(default=False)

    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, default='')

    can_self_assign = models.BooleanField(default=False)

    show_to_alliances = models.ManyToManyField(AllianceSetup, blank=True, related_name='label_groupings')
    show_to_corporations = models.ManyToManyField(CorporationSetup, blank=True, related_name='label_groupings')

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name
