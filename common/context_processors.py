from django.conf import settings

def project_version(request):
    """
    Return project version from settings.
    """
    return {
        'VERSION': getattr(settings, 'VERSION', '1.0.0'),
        'DEVELOPER_NAME': getattr(settings, 'DEVELOPER_NAME', ''),
        'DEVELOPER_URL': getattr(settings, 'DEVELOPER_URL', ''),
    }
