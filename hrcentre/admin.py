from django.contrib import admin

from .models import CorporationSetup, AllianceSetup


@admin.register(CorporationSetup)
class CorporationSetupAdmin(admin.ModelAdmin):
    pass


@admin.register(AllianceSetup)
class AllianceSetupAdmin(admin.ModelAdmin):
    pass
