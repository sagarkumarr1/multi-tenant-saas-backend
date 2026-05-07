# Test-only settings — SQLite use karo, PostgreSQL ki zarurat nahi
from config.settings import *

# Override DB to SQLite in-memory for fast, isolated tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable throttling in tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}
