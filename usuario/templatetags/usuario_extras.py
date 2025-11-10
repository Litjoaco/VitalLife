from django import template

register = template.Library()

@register.filter
def to_css_float(value):
    """
    Convierte un número a un string y reemplaza la coma decimal por un punto
    para que sea compatible con CSS.
    """
    return str(value).replace(',', '.')