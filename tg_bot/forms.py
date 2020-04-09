from django import forms
from .models import *


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            'external_id',
            'name',
        )
        widgets = {
            'name': forms.TextInput,
        }


class PaymentRequestForm(forms.Form):
    chat_id = forms.IntegerField(required=True)
    price = forms.IntegerField(required=True)
    tasks_count = forms.IntegerField(required=True)
    good = forms.IntegerField(required=True)
    bad = forms.IntegerField(required=True)


class PaymentConfirmationForm(forms.Form):
    chat_id = forms.IntegerField(required=True)
    chat_number = forms.IntegerField(required=True)