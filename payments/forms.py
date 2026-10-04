from django import forms

from .models import Dispute, Payment


class CardForm(forms.Form):
    card_number = forms.CharField(max_length=23, label="Card number", help_text="Demo: any 16 digits (ending 0002 = declined)")
    expiry = forms.CharField(max_length=5, label="Expiry (MM/YY)")
    cvv = forms.CharField(max_length=4, widget=forms.PasswordInput)


class ChargeForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ("purpose", "description", "amount")


class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ("reason",)
        widgets = {"reason": forms.Textarea(attrs={"rows": 3})}


class ResolveForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ("status", "resolution")
