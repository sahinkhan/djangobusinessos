from businessos.core.organization.models import Company


def companies_for_user(user):
    if not user.is_authenticated or not user.is_active:
        return Company.objects.none()
    if user.is_superuser:
        return Company.objects.filter(is_active=True)
    return Company.objects.filter(is_active=True, user_accesses__user=user).distinct()
