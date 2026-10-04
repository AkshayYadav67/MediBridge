from datetime import datetime, timedelta

from django.utils import timezone

from .models import Appointment


def available_slots(doctor, day):
    """Free start times for `doctor` on `day`, derived from weekly availability minus booked slots."""
    booked = set(Appointment.objects.filter(doctor=doctor, date=day)
                 .exclude(status=Appointment.Status.CANCELLED).values_list("time", flat=True))
    now = timezone.localtime()
    slots = set()
    for rule in doctor.availability.filter(weekday=day.weekday()):
        cur, end = datetime.combine(day, rule.start_time), datetime.combine(day, rule.end_time)
        step = timedelta(minutes=rule.slot_minutes)
        while cur + step <= end:
            t = cur.time()
            in_future = day > now.date() or (day == now.date() and t > now.time())
            if t not in booked and in_future:
                slots.add(t)
            cur += step
    return sorted(slots)
