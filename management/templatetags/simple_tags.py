from django import template

register = template.Library()


@register.filter
def to_str(value):
    """converts int to string"""
    return str(value)

@register.filter
def get_params_from_path(value):
    return value.split('?')[-1]