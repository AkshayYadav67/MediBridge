from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from appointments.models import Appointment

from .models import ChatMessage


def _get_appt(request, pk):
    appt = get_object_or_404(Appointment.objects.select_related("doctor__user", "patient"), pk=pk)
    if request.user not in (appt.patient, appt.doctor.user):
        raise PermissionDenied
    return appt


@role_required("patient", "doctor")
def room(request, pk):
    appt = _get_appt(request, pk)
    active = appt.status == "confirmed"
    return render(request, "telemedicine/room.html", {
        "appt": appt, "active": active,
        # unguessable per-appointment room name; only the two participants can reach this page
        "video_url": f"{settings.VIDEO_PROVIDER_URL}/medibridge-{appt.room_id.hex}" if active else "",
    })


@role_required("patient", "doctor")
def messages_json(request, pk):
    appt = _get_appt(request, pk)
    after = int(request.GET.get("after", 0) or 0)
    msgs = appt.messages.filter(id__gt=after).select_related("sender")
    return JsonResponse({"messages": [{
        "id": m.id, "body": m.body, "mine": m.sender_id == request.user.id,
        "sender": m.sender.display_name, "at": m.created_at.strftime("%H:%M")} for m in msgs]})


@require_POST
@role_required("patient", "doctor")
def send_message(request, pk):
    appt = _get_appt(request, pk)
    body = request.POST.get("body", "").strip()[:2000]
    if not body or appt.status == "cancelled":
        return JsonResponse({"ok": False}, status=400)
    m = ChatMessage.objects.create(appointment=appt, sender=request.user, body=body)
    return JsonResponse({"ok": True, "id": m.id})
