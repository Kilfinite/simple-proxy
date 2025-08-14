from app import app as application

# For gunicorn: gunicorn -w 2 -b 0.0.0.0:5001 wsgi:application