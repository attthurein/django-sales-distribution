from django import template

register = template.Library()

@register.filter(name='is_equal_to')
def is_equal_to(value, arg):
    """
    Custom filter to compare equality without using == in templates
    to bypass aggressive minifiers that strip spaces.
    """
    try:
        return str(value) == str(arg)
    except (ValueError, TypeError):
        return False
