from django.db.models.signals import post_save
from django.dispatch import receiver

from allianceauth.authentication.models import CharacterOwnership

from corptools.models import CharacterAudit

from .models import CorporationSetup, AllianceSetup
from .tasks import update_character_login


@receiver(post_save, sender=CharacterAudit)
def update_login_data(sender, instance: CharacterAudit, **kwargs):
    if CorporationSetup.objects.filter(
        corporation__corporation_id__in=CharacterOwnership.objects.filter(user=instance.character.character_ownership.user).values('character__corporation_id')
    ).exists() or AllianceSetup.objects.filter(
        alliance__alliance_id__in=CharacterOwnership.objects.filter(user=instance.character.character_ownership.user).values('character__alliance_id')
    ).exists():
        update_character_login.apply_async(kwargs={'pk': instance.pk, 'force_refresh': False}, countdown=30)
