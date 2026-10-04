from django import forms

from .models import MedicalRecord, TestResult


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ("diagnosis", "treatment", "notes")
        widgets = {f: forms.Textarea(attrs={"rows": 3}) for f in fields}


class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = ("name", "result", "reference_range", "report_file", "test_date")
        widgets = {"test_date": forms.DateInput(attrs={"type": "date"}), "result": forms.Textarea(attrs={"rows": 3})}
