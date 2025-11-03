from django import template

register = template.Library()

@register.filter
def get_item(sequence, key):
    try:
        return sequence[key]
    except (IndexError, TypeError, KeyError):
        return None