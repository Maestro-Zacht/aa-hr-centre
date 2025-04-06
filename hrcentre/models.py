from django.db import models
from django.contrib.auth.models import Group, User

from allianceauth.eveonline.models import EveCorporationInfo, EveAllianceInfo

from corptools.models import CharacterAudit


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
    characteraudit = models.OneToOneField(CharacterAudit, on_delete=models.CASCADE, related_name='login_data')
    last_login = models.DateTimeField(null=True, blank=True)
    last_update = models.DateTimeField(null=True, blank=True)
