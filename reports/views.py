import csv

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import DoctorProfile
from appointments.models import Appointment, Feedback
from notifications.models import Notification
from notifications.services import notify
from payments.forms import ResolveForm
from payments.gateway import get_gateway
from payments.models import Dispute, Payment

User = get_user_model()
ADMINS = ("admin", "staff")


@role_required(*ADMINS)
def dashboard(request):
    paid = Payment.objects.filter(status="paid")
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    ctx = {
        "users": User.objects.values("role").annotate(n=Count("id")),
        "appt_status": Appointment.objects.values("status").annotate(n=Count("id")),
        "revenue_total": paid.aggregate(s=Sum("amount"))["s"] or 0,
        "revenue_monthly": paid.annotate(m=TruncMonth("created_at")).values("m").annotate(s=Sum("amount")).order_by("-m")[:12],
        "avg_rating": Feedback.objects.aggregate(a=Avg("rating"))["a"],
        "feedback": Feedback.objects.select_related("appointment__doctor__user").order_by("-created_at")[:8],
        "top_doctors": DoctorProfile.objects.annotate(n=Count("appointments")).order_by("-n")[:5],
        "pending_doctors": DoctorProfile.objects.filter(is_approved=False).select_related("user"),
        "open_disputes": Dispute.objects.filter(status="open").count(),
        "health": {"database": db_ok,
                   "failed_emails": Notification.objects.filter(email_sent=False, user__email__gt="").count(),
                   "unread_notifications": Notification.objects.filter(is_read=False).count()},
    }
    return render(request, "reports/dashboard.html", ctx)


@role_required(*ADMINS)
def user_list(request):
    qs = User.objects.all().order_by("role", "username")
    role = request.GET.get("role")
    if role:
        qs = qs.filter(role=role)
    return render(request, "reports/users.html", {"users": qs, "role": role})


@require_POST
@role_required(*ADMINS)
def toggle_user(request, pk):
    u = get_object_or_404(User, pk=pk)
    if u.is_superuser and not request.user.is_superuser:
        messages.error(request, "Only superusers can change superuser accounts.")
    else:
        u.is_active = not u.is_active
        u.save(update_fields=["is_active"])
        messages.success(request, f"{u.username} is now {'active' if u.is_active else 'deactivated'}.")
    return redirect("reports:users")


@require_POST
@role_required(*ADMINS)
def approve_doctor(request, pk):
    d = get_object_or_404(DoctorProfile, pk=pk)
    d.is_approved = True
    d.save(update_fields=["is_approved"])
    notify(d.user, "Profile approved", "Your doctor profile was approved. Patients can now book you.")
    messages.success(request, f"{d} approved.")
    return redirect("reports:dashboard")


@role_required(*ADMINS)
def disputes(request):
    return render(request, "reports/disputes.html", {"disputes": Dispute.objects.select_related("payment", "raised_by")})


@role_required(*ADMINS)
def resolve_dispute(request, pk):
    d = get_object_or_404(Dispute, pk=pk)
    form = ResolveForm(request.POST or None, instance=d)
    if request.method == "POST" and form.is_valid():
        d = form.save()
        if d.status == "refunded" and d.payment.status == "paid":
            get_gateway().refund(d.payment.transaction_id)
            d.payment.status = "refunded"
            d.payment.save(update_fields=["status"])
        notify(d.raised_by, "Dispute update", f"Your dispute is now: {d.get_status_display()}. {d.resolution}", kind="payment")
        messages.success(request, "Dispute updated.")
        return redirect("reports:disputes")
    return render(request, "form.html", {"form": form, "title": f"Resolve dispute #{d.pk}", "submit": "Save"})


@role_required(*ADMINS)
def export_csv(request, kind):
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="{kind}.csv"'
    w = csv.writer(resp)
    if kind == "appointments":
        w.writerow(["id", "patient", "doctor", "date", "time", "mode", "status"])
        for a in Appointment.objects.select_related("patient", "doctor__user"):
            w.writerow([a.id, a.patient.username, a.doctor.user.username, a.date, a.time, a.mode, a.status])
    elif kind == "payments":
        w.writerow(["id", "user", "purpose", "amount", "status", "transaction_id", "created_at"])
        for p in Payment.objects.select_related("user"):
            w.writerow([p.id, p.user.username, p.purpose, p.amount, p.status, p.transaction_id, p.created_at])
    elif kind == "feedback":
        w.writerow(["appointment", "doctor", "rating", "comment"])
        for f in Feedback.objects.select_related("appointment__doctor__user"):
            w.writerow([f.appointment_id, f.appointment.doctor.user.username, f.rating, f.comment])
    else:
        return HttpResponse(status=404)
    return resp
