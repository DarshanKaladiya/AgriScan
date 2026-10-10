from core.translations import get_translation, AVAILABLE_LANGUAGES

def language_context(request):
    """
    Injects active language dictionary and helper attributes into all templates.
    Checks session first, then cookie, with fallback to 'en'.
    """
    lang = request.session.get('lang') or request.COOKIES.get('agri_lang') or 'en'
    if lang not in ['en', 'hi', 'gu']:
        lang = 'en'
        
    return {
        't': get_translation(lang),
        'current_lang': lang,
        'available_languages': AVAILABLE_LANGUAGES,
    }
