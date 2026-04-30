import os
import subprocess
from django.db import connection


class VercelDBMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._initialized = False

    def __call__(self, request):
        if not self._initialized and os.getenv('VERCEL'):
            self._init_db()
            self._initialized = True
        return self.get_response(request)

    def _init_db(self):
        db_path = '/tmp/db.sqlite3'
        if not os.path.exists(db_path):
            try:
                open(db_path, 'a').close()
                os.chmod(db_path, 0o666)
            except Exception:
                pass
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            pass
