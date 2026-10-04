from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import can_access_patient, role_required
from appointments.models import Appointment
from notifications.services import notify

from .forms import ItemFormSet, OrderForm, PrescriptionForm
from .models import Prescription


@role_required("patient", "doctor", "staff", "admin")
def prescription_list(request):
    qs = Prescription.objects.select_related("doctor__user", "patient")
    u = request.user
    if u.is_patient:
        qs = qs.filter(patient=u)
    elif u.is_doctor:
        qs = qs.filter(doctor__user=u)
    return render(request, "prescriptions/list.html", {"prescriptions": qs})


@role_required("patient", "doctor", "staff", "admin")
def prescription_detail(request, pk):
    rx = get_object_or_404(Prescription.objects.select_related("doctor__user", "patient"), pk=pk)
    if not can_access_patient(request.user, rx.patient):
        raise PermissionDenied
    return render(request, "prescriptions/detail.html", {"rx": rx, "orders": rx.orders.select_related("pharmacy")})


@role_required("doctor")
def prescription_create(request, appointment_id):
    appt = get_object_or_404(Appointment, pk=appointment_id, doctor__user=request.user)
    rx = Prescription(patient=appt.patient, doctor=appt.doctor, appointment=appt)
    form = PrescriptionForm(request.POST or None, instance=rx)
    formset = ItemFormSet(request.POST or None, instance=rx)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        rx = form.save()
        formset.instance = rx
        items = [f for f in formset.save(commit=False)]
        if not items:
            rx.delete()
            messages.error(request, "Add at least one medicine.")
            return redirect("prescriptions:create", appointment_id=appt.pk)
        for i in items:
            i.prescription = rx
            i.save()
        notify(appt.patient, "New prescription", f"{appt.doctor} issued a prescription.", kind="prescription",
               link=f"/prescriptions/{rx.pk}/", send_sms=True)
        messages.success(request, "Prescription issued.")
        return redirect("prescriptions:detail", pk=rx.pk)
    return render(request, "prescriptions/create.html", {"form": form, "formset": formset, "appt": appt})


@role_required("patient")
def order_pharmacy(request, pk):
    rx = get_object_or_404(Prescription, pk=pk, patient=request.user)
    form = OrderForm(request.POST or None, initial={
        "contact_phone": request.user.phone,
        "delivery_address": getattr(getattr(request.user, "patient_profile", None), "address", "")})
    if request.method == "POST" and form.is_valid():
        order = form.save(commit=False)
        order.prescription = rx
        order.save()
        if order.pharmacy.email:
            from django.core.mail import send_mail
            from django.conf import settings
            body = f"New home-delivery order for Rx #{rx.pk}\nDeliver to: {order.delivery_address}\nPhone: {order.contact_phone}\n\n" + \
                   "\n".join(f"- {i.medicine} {i.dosage}, {i.frequency}, {i.duration_days} days" for i in rx.items.all())
            send_mail(f"MediBridge order #{order.pk}", body, settings.DEFAULT_FROM_EMAIL, [order.pharmacy.email], fail_silently=True)
        notify(request.user, "Pharmacy order placed", f"Your order with {order.pharmacy} was placed.", kind="prescription")
        messages.success(request, "Prescription sent to the pharmacy for home delivery.")
        return redirect("prescriptions:detail", pk=rx.pk)
    return render(request, "form.html", {"form": form, "title": "Order medicines for home delivery", "submit": "Send to pharmacy"})
