from django import forms
from .models import *


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            'external_id',
            'name',
            'balance',
            'promo_code',
            'keywords'
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


class MoneyOutRequestConfirmationForm(forms.Form):
    request_id = forms.IntegerField(required=True)


class ApproveOrderForm(forms.Form):
    order_id = forms.IntegerField(required=True)


class MassMailForm(forms.Form):
    text = forms.CharField(required=True, widget=forms.Textarea)


class MessageFromSupportForm(forms.Form):
    user_id = forms.IntegerField(required=True)
    text = forms.CharField(required=True)


class OrderFeedbackForm(forms.Form):
    order_id = forms.IntegerField(required=True)
    price = forms.IntegerField(required=True)
    comment = forms.CharField(required=True)
