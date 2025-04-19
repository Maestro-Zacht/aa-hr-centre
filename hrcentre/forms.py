from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Label


class UserLabelsForm(forms.Form):
    labels = forms.ModelMultipleChoiceField(
        queryset=Label.objects.all(),
        label=_('Labels'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
