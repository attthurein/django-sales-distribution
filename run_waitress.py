
import os
import django
from waitress import serve
from django.core.wsgi import get_wsgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_distribution.settings.development')

# Setup Django
django.setup()

# Get the WSGI application
application = get_wsgi_application()

if __name__ == '__main__':
    print("Serving on http://localhost:8000")
    serve(application, host='0.0.0.0', port=8000)
