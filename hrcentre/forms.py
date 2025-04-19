from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Label, UserNotes


class UserLabelsForm(forms.Form):
    labels = forms.ModelMultipleChoiceField(
        queryset=Label.objects.all(),
        label=_('Labels'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class UserNotesForm(forms.ModelForm):
    class Meta:
        model = UserNotes
        fields = ['notes']
        labels = {
            'notes': _('Notes'),
        }
