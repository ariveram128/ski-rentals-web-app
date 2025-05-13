from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def decimal_multiply(value, arg):
    """Multiplies the Decimal value by the argument"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except:
        return value

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using the key.
    
    Usage: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    
    return dictionary.get(str(key)) if isinstance(key, int) else dictionary.get(key)

@register.filter
def sum_values(iterable, property_name=None):
    """
    Sum all values in an iterable.
    If property_name is provided, sum that property from all objects in the iterable.
    
    Usage: {{ iterable|sum_values }} or {{ iterable|sum_values:"property_name" }}
    """
    try:
        total = 0
        for item in iterable:
            if property_name:
                # Extract the property from the item
                value = getattr(item, property_name, 0)
            else:
                value = item
            total += float(value)
        return total
    except:
        return 0

@register.filter
def attr(field, attr_args):
    """
    Set HTML attributes on a form field.
    
    Usage: {{ form.field|attr:"class:form-control" }}
    Multiple attributes: {{ form.field|attr:"class:form-control,placeholder:Enter value" }}
    """
    attrs = {}
    
    # Parse the attribute arguments
    for arg in attr_args.split(','):
        if ':' in arg:
            key, value = arg.split(':', 1)
            attrs[key.strip()] = value.strip()
    
    # Check if field is a form field or already rendered string
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs=attrs)
    else:
        # For SafeString or other non-form fields, return as is
        return field

@register.filter
def div(value, arg):
    """
    Divides the value by the argument
    
    Usage: {{ value|div:8 }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return value 