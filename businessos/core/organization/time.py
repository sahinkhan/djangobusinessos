from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Company


def company_timezone(company_id: UUID) -> ZoneInfo:
    """Return the configured IANA timezone for a company identity."""
    timezone_name = Company.objects.filter(id=company_id).values_list("timezone", flat=True).first()
    if timezone_name is None:
        raise ValidationError("The company does not exist.")
    return ZoneInfo(timezone_name)


def company_local_datetime(company_id: UUID, instant: datetime | None = None) -> datetime:
    """Convert an aware storage timestamp (UTC by convention) to company-local time."""
    value = instant or timezone.now()
    if timezone.is_naive(value):
        raise ValidationError("Business-time conversion requires a timezone-aware datetime.")
    return value.astimezone(company_timezone(company_id))


def company_local_date(company_id: UUID, instant: datetime | None = None):
    return company_local_datetime(company_id, instant).date()
