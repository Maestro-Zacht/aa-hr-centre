from celery import shared_task
from celery_once import QueueOnce

from django.utils import timezone

from corptools.models import CharacterAudit
from corptools.task_helpers.char_tasks import get_token

from .models import CharacterAuditLoginData
from .provider import esi


@shared_task(base=QueueOnce, once={'keys': ['pk'], 'graceful': True})
def update_character_login(pk, force_refresh=False):
    char = CharacterAudit.objects.get(pk=pk)
    login_data = CharacterAuditLoginData.objects.get_or_create(characteraudit=char)[0]

    if force_refresh or login_data.last_update is None or login_data.last_update < timezone.now() - timezone.timedelta(hours=1):
        token = get_token(char.character.character_id, ['esi-location.read_online.v1'])
        if token:
            result = (
                esi.client
                .Location
                .get_characters_character_id_online(
                    character_id=char.character.character_id,
                    token=token.valid_access_token()
                )
                .results()
            )
            if result['online']:
                login_data.last_login = timezone.now()
                login_data.last_update = timezone.now()
            elif 'last_login' in result:
                login_data.last_login = result['last_login']
                login_data.last_update = timezone.now()
            login_data.save()
