"""Role-based access control helpers."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles and not request.user.is_superuser:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def can_access_patient(user, patient):
    """Patients see themselves; doctors only patients they have an appointment with; admins everyone."""
    from appointments.models import Appointment
    if user.pk == patient.pk or user.is_admin_role or user.is_superuser:
        return True
    if user.is_doctor and hasattr(user, "doctor_profile"):
        return Appointment.objects.filter(doctor=user.doctor_profile, patient=patient).exists()
    return False
