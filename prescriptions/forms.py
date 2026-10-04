from django import forms
from django.forms import inlineformset_factory

from .models import Pharmacy, Prescription, PrescriptionItem, PharmacyOrder


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ("diagnosis", "notes", "refill_date")
        widgets = {"refill_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 2})}


ItemFormSet = inlineformset_factory(Prescription, PrescriptionItem,
                                    fields=("medicine", "dosage", "frequency", "duration_days", "instructions"),
                                    extra=3, can_delete=False)


class OrderForm(forms.ModelForm):
    class Meta:
        model = PharmacyOrder
        fields = ("pharmacy", "delivery_address", "contact_phone")
        widgets = {"delivery_address": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["pharmacy"].queryset = Pharmacy.objects.filter(is_active=True)
