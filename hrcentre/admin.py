from django.contrib import admin

from .models import CorporationSetup, AllianceSetup, Label, UsersCheck, LabelGrouping


@admin.register(CorporationSetup)
class CorporationSetupAdmin(admin.ModelAdmin):
    pass


@admin.register(AllianceSetup)
class AllianceSetupAdmin(admin.ModelAdmin):
    pass


@admin.register(UsersCheck)
class UsersCheckAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', )
    search_fields = ('name', 'description', )


class MandatoryMixin:
    validate_min = True

    def get_formset(self, *args, **kwargs):
        return super().get_formset(validate_min=self.validate_min, *args, **kwargs)


class LabelInline(MandatoryMixin, admin.TabularInline):
    model = Label
    min_num = 1
    extra = 0
    validate_min = True


@admin.register(LabelGrouping)
class LabelGroupingAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'can_self_assign', )
    search_fields = ('name', 'description', )
    list_filter = ('can_self_assign', )
    inlines = [LabelInline]
