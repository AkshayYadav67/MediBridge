from datetime import datetime

from django import forms

from .models import Appointment, Feedback


class BookingForm(forms.Form):
    date = forms.DateField(widget=forms.HiddenInput)
    time = forms.ChoiceField()
    mode = forms.ChoiceField(choices=Appointment.Mode.choices)
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="Reason for visit")

    def __init__(self, *args, slots=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["time"].choices = [(t.strftime("%H:%M"), t.strftime("%H:%M")) for t in slots]

    def clean_time(self):
        return datetime.strptime(self.cleaned_data["time"], "%H:%M").time()


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("rating", "comment")
