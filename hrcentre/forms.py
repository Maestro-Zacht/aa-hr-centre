from django import forms
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.db.models import Count
from django.utils.translation import gettext_lazy as _


from .models import Label, UserNotes, LabelGrouping


class ButtonGroupMixin:
    template_name = 'hrcentre/widgets/button_group_multiple_input.html'
    option_template_name = 'hrcentre/widgets/button_group_input_option.html'

    def create_option(self, *args, **kwargs):
        res = super().create_option(*args, **kwargs)

        value = args[1]

        if isinstance(value, str):
            res['hrcentre_label_class'] = 'btn btn-outline-secondary'
        else:
            label: Label = value.instance
            res['hrcentre_label_class'] = f'btn {label.form_bs_class}'

        return res


class RadioSelectButtonGroup(ButtonGroupMixin, forms.RadioSelect):
    pass


class CheckboxSelectButtonGroup(ButtonGroupMixin, forms.CheckboxSelectMultiple):
    pass


class LabelGroupingChoiceForm(forms.Form):
    def __init__(self, user: User, groupings: QuerySet[LabelGrouping], *args, **kwargs):
        super().__init__(*args, **kwargs)

        for grouping in groupings.annotate(_options_count=Count('options')):
            if grouping.multiple_selection or grouping._options_count == 1:
                self.fields[grouping.name] = forms.ModelMultipleChoiceField(
                    queryset=Label.objects.filter(grouping=grouping),
                    initial=Label.objects.filter(user_labels__user=user, grouping=grouping),
                    label=grouping.name,
                    widget=CheckboxSelectButtonGroup,
                    required=not grouping.allow_empty,
                    help_text=grouping.form_help_text,
                )
            else:
                self.fields[grouping.name] = forms.ModelChoiceField(
                    queryset=Label.objects.filter(grouping=grouping),
                    initial=Label.objects.filter(user_labels__user=user, grouping=grouping).first(),
                    label=grouping.name,
                    widget=RadioSelectButtonGroup,
                    blank=grouping.allow_empty,
                    required=not grouping.allow_empty,
                    help_text=grouping.form_help_text,
                )


class UserNotesForm(forms.ModelForm):
    class Meta:
        model = UserNotes
        fields = ['notes']
        labels = {
            'notes': _('Notes'),
        }
