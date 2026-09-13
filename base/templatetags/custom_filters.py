from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies value by arg safely"""
    try:
        if value is None or arg is None:
            return 0.0
        return round(float(value) * float(arg), 2)
    except (ValueError, TypeError):
        return 0.0

@register.filter
def subtract(value, arg):
    """Subtracts arg from value safely"""
    try:
        if value is None:
            value = 0.0
        if arg is None:
            arg = 0.0
        return round(float(value) - float(arg), 2)
    except (ValueError, TypeError):
        return 0.0

@register.filter
def currency(value):
    """Formats number as currency"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"
