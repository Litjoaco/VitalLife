from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Custom filter to retrieve an item from a dictionary or list by its key/index.
    Usage: {{ my_dict|get_item:key }} or {{ my_list|get_item:index }}
    """
    try:
        return dictionary[key]
    except (KeyError, IndexError):
        return None