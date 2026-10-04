from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import can_access_patient, role_required
from appointments.models import Appointment
from notifications.services import notify

from .forms import CardForm, ChargeForm, DisputeForm
from .gateway import get_gateway
from .models import Dispute, Payment

User = get_user_model()


@role_required("patient")
def pay_appointment(request, appointment_id):
    appt = get_object_or_404(Appointment, pk=appointment_id, patient=request.user)
    if appt.is_paid:
        messages.info(request, "This consultation is already paid.")
        return redirect("appointments:detail", pk=appt.pk)
    payment = Payment.objects.filter(user=request.user, appointment=appt, purpose="consultation",
                                     status__in=["pending", "failed"]).first()
    if payment is None:
        payment = Payment.objects.create(user=request.user, appointment=appt, purpose="consultation",
                                         amount=appt.fee, description=f"Consultation with {appt.doctor}")
    return redirect("payments:pay", pk=payment.pk)


@role_required("patient")
def pay(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    if payment.status == "paid":
        return redirect("payments:history")
    form = CardForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        result = get_gateway().charge(payment.amount, form.cleaned_data["card_number"])
        if result.success:
            payment.status, payment.transaction_id, payment.method = "paid", result.transaction_id, "card"
            payment.save()
            notify(request.user, "Payment received", f"Payment of {payment.amount} received. Ref {payment.transaction_id}.",
                   kind="payment")
            messages.success(request, "Payment successful.")
            return redirect("payments:history")
        payment.status = "failed"
        payment.save(update_fields=["status"])
        messages.error(request, result.error)
    return render(request, "payments/checkout.html", {"payment": payment, "form": form})


@role_required("patient", "doctor", "staff", "admin")
def history(request):
    u = request.user
    qs = Payment.objects.select_related("appointment", "user")
    if u.is_patient:
        qs = qs.filter(user=u)
    elif u.is_doctor:
        qs = qs.filter(appointment__doctor__user=u)
    return render(request, "payments/history.html", {"payments": qs})


@role_required("doctor")
def create_charge(request, patient_id):
    patient = get_object_or_404(User, pk=patient_id, role="patient")
    if not can_access_patient(request.user, patient):
        return redirect("accounts:dashboard")
    form = ChargeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        p = form.save(commit=False)
        p.user = patient
        p.save()
        notify(patient, "New charge", f"{p.description or p.get_purpose_display()}: {p.amount} due.", kind="payment",
               link="/payments/")
        messages.success(request, "Charge sent to patient.")
        return redirect("records:patient", patient_id=patient.pk)
    return render(request, "form.html", {"form": form, "title": f"Charge {patient.display_name}", "submit": "Send charge"})


@role_required("patient")
def raise_dispute(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user, status="paid")
    form = DisputeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.save(commit=False)
        d.payment, d.raised_by = payment, request.user
        d.save()
        messages.success(request, "Dispute submitted. An administrator will review it.")
        return redirect("payments:history")
    return render(request, "form.html", {"form": form, "title": "Dispute this payment", "submit": "Submit dispute"})
