from django import forms
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from .models import Label, UserNotes, LabelGrouping, UserLabel


class LabelGroupingChoiceForm(forms.Form):
    def __init__(self, user: User, groupings: QuerySet[LabelGrouping], *args, **kwargs):
        super().__init__(*args, **kwargs)

        for grouping in groupings.annotate(_options_count=Count('options')):
            if grouping.multiple_selection or grouping._options_count == 1:
                self.fields[grouping.name] = forms.ModelMultipleChoiceField(
                    queryset=Label.objects.filter(grouping=grouping),
                    initial=Label.objects.filter(user_labels__user=user, grouping=grouping),
                    label=grouping.name,
                    widget=forms.CheckboxSelectMultiple,
                    required=False,
                )
            else:
                self.fields[grouping.name] = forms.ModelChoiceField(
                    queryset=Label.objects.filter(grouping=grouping),
                    initial=Label.objects.filter(user_labels__user=user, grouping=grouping).first(),
                    label=grouping.name,
                    widget=forms.RadioSelect,
                    blank=True,
                    required=False,
                )


class UserNotesForm(forms.ModelForm):
    class Meta:
        model = UserNotes
        fields = ['notes']
        labels = {
            'notes': _('Notes'),
        }
