from django.contrib import messages
from django.shortcuts import redirect

from .models import UserAccount


def get_current_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return (
            UserAccount.objects.select_related('customer_profile', 'organizer_profile')
            .prefetch_related('roles__role')
            .get(pk=user_id)
        )
    except UserAccount.DoesNotExist:
        request.session.flush()
        return None


def get_role_name(user):
    return user.role_name if user else ''


def build_base_context(request):
    user = get_current_user(request)
    role_name = get_role_name(user)
    return {
        'current_user': user,
        'current_role': role_name,
        'is_logged_in': bool(user),
        'is_admin': role_name == 'admin',
        'is_organizer': role_name == 'organizer',
        'is_customer': role_name == 'customer',
    }


def ensure_logged_in(request):
    if get_current_user(request):
        return None
    messages.error(request, 'Silakan login terlebih dahulu.')
    return redirect('pengguna:login')


def ensure_roles(request, *allowed_roles):
    user = get_current_user(request)
    if not user:
        messages.error(request, 'Silakan login terlebih dahulu.')
        return redirect('pengguna:login')
    if user.role_name not in allowed_roles:
        messages.error(request, 'Anda tidak memiliki akses ke halaman tersebut.')
        return redirect('pengguna:dashboard')
    return None
