DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True,  # ← 추가!
        'OPTIONS': {
            'timeout': 30,  # ← 30초 대기
            'check_same_thread': False,  # ← 멀티스레드 허용
        }
    }
}