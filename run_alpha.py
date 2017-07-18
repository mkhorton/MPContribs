# http://flask.pocoo.org/docs/0.10/patterns/appdispatch/
from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware, SharedDataMiddleware
from materials_django.wsgi import application as django_app
from materials_django.settings import STATIC_ROOT_URLS

if __name__ == '__main__':
    application = SharedDataMiddleware(django_app, STATIC_ROOT_URLS)
    run_simple('0.0.0.0', 7005, application, use_reloader=False,
               use_debugger=False, use_evalex=False, threaded=False)
