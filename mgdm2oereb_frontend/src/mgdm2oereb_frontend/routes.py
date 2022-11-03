# -*- coding: utf-8 -*-

from mgdm2oereb_frontend.views.form import Form
from mgdm2oereb_frontend.views.index import Index
from mgdm2oereb_frontend.views.delivery import Delivery
from mgdm2oereb_frontend.views.status import Status
from mgdm2oereb_frontend.views.error import Error


def includeme(config):
    """Route and view definitions used by this application.

    Args:
        config (pyramid.config.Configurator): The application's configuration object.

    """

    config.add_static_view('static', 'mgdm2oereb_frontend:static')

    config.add_route('delivery', '/get/{egrid}/{job_id}')
    config.add_view(Delivery,
                    attr='render_html',
                    route_name='delivery',
                    renderer='mgdm2oereb_frontend:templates/delivery.html',
                    request_method='GET')

    config.add_route('status', '/status/{egrid}/{job_id}')
    config.add_view(Status,
                    attr='render_html',
                    route_name='status',
                    renderer='mgdm2oereb_frontend:templates/status.html',
                    request_method='GET')

    config.add_route('error', '/error/{egrid}/{job_id}')
    config.add_view(Error,
                    attr='render_html',
                    route_name='error',
                    renderer='mgdm2oereb_frontend:templates/error.html',
                    request_method='GET')

    config.add_route('index', '/')
    config.add_view(Index,
                    attr='render_html',
                    route_name='index',
                    renderer='mgdm2oereb_frontend:templates/index.html',
                    request_method='GET')

    config.add_route('form', '/upload')
    config.add_view(Form,
                    attr='upload',
                    route_name='form',
                    request_method='POST')

    config.commit()
