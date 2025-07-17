from django.contrib import admin

from .models import CorporationSetup, AllianceSetup, Label, UsersCheck, LabelGrouping


class SetupAdmin(admin.ModelAdmin):
    filter_horizontal = ('access_list', 'checks', )


@admin.register(CorporationSetup)
class CorporationSetupAdmin(SetupAdmin):
    pass


@admin.register(AllianceSetup)
class AllianceSetupAdmin(SetupAdmin):
    pass


@admin.register(UsersCheck)
class UsersCheckAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', )
    search_fields = ('name', 'description', )


class ValidateMinMixin:
    validate_min = True

    def get_formset(self, *args, **kwargs):
        return super().get_formset(validate_min=self.validate_min, *args, **kwargs)


class LabelInline(ValidateMinMixin, admin.TabularInline):
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
