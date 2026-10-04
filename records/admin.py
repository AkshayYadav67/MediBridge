from django.contrib import admin

from .models import MedicalRecord, TestResult

admin.site.register(MedicalRecord)
admin.site.register(TestResult)
