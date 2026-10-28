from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """Sadece müşteri rolündeki kullanıcılar erişebilir."""
    message = 'Bu işlem sadece müşteriler için.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'CUSTOMER'
        )


class IsDriver(permissions.BasePermission):
    """Sadece sürücü rolündeki kullanıcılar erişebilir."""
    message = 'Bu işlem sadece sürücüler için.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'DRIVER'
        )


class IsVerifiedDriver(permissions.BasePermission):
    """Sürücü ve admin onaylı olmalı."""
    message = 'Sürücü hesabınız henüz onaylanmadı.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'DRIVER'
            and request.user.is_verified_driver
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Nesne sahibi olmayan kullanıcılar sadece OKUYABİLİR.
    'author', 'user' veya 'customer' alanı olan modellerle çalışır.
    """
    message = 'Bu işlem için bu nesnenin sahibi olmalısınız.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        owner = (
            getattr(obj, 'author', None)
            or getattr(obj, 'user', None)
            or getattr(obj, 'customer', None)
        )
        return owner == request.user