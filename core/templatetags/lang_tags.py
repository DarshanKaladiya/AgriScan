from django import template

register = template.Library()

@register.filter(name='get_lang')
def get_lang(val, lang='en'):
    """
    If val is a dictionary with language keys (like {'en': '...', 'hi': '...', 'gu': '...'}),
    returns the value for the requested language with fallback to English or the first available key.
    If val is a plain string, returns val directly.
    """
    if isinstance(val, dict):
        return val.get(lang) or val.get('en') or next(iter(val.values()), '')
    return val

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Safely retrieves a dictionary key within Django templates."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''
