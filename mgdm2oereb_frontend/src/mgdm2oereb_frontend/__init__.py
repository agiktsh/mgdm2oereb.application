# -*- coding: utf-8 -*-
import logging
import os
from distutils.util import strtobool
from pprint import pformat

from pyramid.config import Configurator
from pyramid_mako import add_mako_renderer


__VERSION__ = '1.1.3'


route_prefix = None
log = logging.getLogger('mgdm2oereb_frontend')


def main(global_config, **settings):  # pragma: no cover
    """
    This function returns a Pyramid WSGI application. This is necessary for development of
    your plugin. So you can run it local with the paster server and in a IDE like PyCharm. It
    is intended to leave this section as is and do configuration in the includeme section only.
    Push additional configuration in this section means it will not be used by the production
    environment at all!
    """
    settings.update({
        'redis': {
            'host': os.environ.get('REDIS_HOST'),
            'port': int(os.environ.get('REDIS_PORT') or '6379'),
            'db': int(os.environ.get('REDIS_DB') or '0')
        },
        'print_url': os.environ.get('PRINT_URL'),
        'job_max_age': int(os.environ.get('JOB_MAX_AGE') or '3600'),
        'use_test_data': bool(strtobool(os.environ.get('USE_TEST_DATA') or 'false')),
        'proxy': {}
    })
    if 'HTTP_PROXY' in os.environ:
        settings.get('proxy').update({
            'http': os.environ.get('HTTP_PROXY')
        })
    if 'HTTPS_PROXY' in os.environ:
        settings.get('proxy').update({
            'https': os.environ.get('HTTPS_PROXY')
        })

    config = Configurator(settings=settings)

    log_level = '{0}'.format(os.environ.get('LOG_LEVEL')).lower()
    if log_level == 'error':
        log.setLevel(logging.ERROR)
    elif log_level == 'warning':
        log.setLevel(logging.WARNING)
    elif log_level == 'debug':
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    development = os.environ.get('DEVELOPMENT')
    if development is not None and development.lower() in ('true', 'yes', 'on'):
        config.include('pyramid_debugtoolbar')
        log.setLevel(logging.DEBUG)

    log.info('Initialize application mgdm2oereb_frontend, version {0}'.format(__VERSION__))
    log.debug('Configuration:\n{0}'.format(pformat(settings)))

    config.include('mgdm2oereb_frontend')
    config.scan()

    log.info('Application mgdm2oereb_frontend is ready...'.format(__VERSION__))

    return config.make_wsgi_app()


def includeme(config):  # pragma: no cover
    """
    This is the place where you should push all the initial stuff for the plugin
    Args:
        config (pyramid.config.Configurator): The configurator object from the including pyramid module.
    """
    # If you need access to the settings in this part, you can get them via
    # settings = config.get_settings()
    global route_prefix, ownership_queue, gbix_queue, ownership_jobs, right_translations

    route_prefix = config.route_prefix

    config.include('pyramid_mako')

    # bind the mako renderer to other file extensions
    add_mako_renderer(config, ".html")

    config.include('mgdm2oereb_frontend.routes')

    def get_route_prefix(request):
        return config.route_prefix

    config.add_request_method(get_route_prefix, name='route_prefix', reify=True)
