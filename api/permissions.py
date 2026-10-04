from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    roles = ()

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.role in self.roles or u.is_superuser))


class IsPatient(HasRole):
    roles = ("patient",)


class IsDoctor(HasRole):
    roles = ("doctor",)
