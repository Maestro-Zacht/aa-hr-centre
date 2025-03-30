from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required

from .models import CorporationSetup, AllianceSetup


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
