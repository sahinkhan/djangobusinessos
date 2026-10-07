from django import template

from businessos.core.organization.time import company_local_datetime

register = template.Library()


@register.filter
def invoice_amount(value, places):
    return format(value, f".{int(places)}f")


@register.filter
def invoice_local_time(value, company_id):
    return company_local_datetime(company_id, value).strftime("%Y-%m-%d %H:%M:%S %Z")
