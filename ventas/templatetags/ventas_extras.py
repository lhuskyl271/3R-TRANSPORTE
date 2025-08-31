from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Returns the value from a dictionary for a given key.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None