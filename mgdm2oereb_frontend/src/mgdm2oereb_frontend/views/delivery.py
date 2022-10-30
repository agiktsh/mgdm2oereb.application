# -*- coding: utf-8 -*-
import logging
import redis
import pkg_resources

from base64 import b64encode
from json import dumps, loads
from mako.lookup import TemplateLookup
from mako.template import Template
from pyramid.httpexceptions import HTTPFound


log = logging.getLogger('mgdm2oereb_frontend')


class Delivery(object):

    __ownership_template_text = """
    % for ownership in ownerships:
    <%include file="ownership_print.html" args="ownership=ownership" />
    % endfor
    """

    __template_lookup = TemplateLookup(directories=[
        pkg_resources.resource_filename('mgdm2oereb_frontend', 'templates')
    ])

    __ownership_template = Template(__ownership_template_text, lookup=__template_lookup)

    def __init__(self, request):
        """Entry point for index rendering.

        Args:
            request (pyramid.request.Request): The request instance.

        """
        self._request = request
        self._config = request.registry.settings

    def render_html(self):
        pass
