# -*- coding: utf-8 -*-
import logging
import redis

from pyramid.httpexceptions import HTTPFound


log = logging.getLogger('mgdm2oereb_frontend')


class Error(object):
    def __init__(self, request):
        """Entry point for index rendering.

        Args:
            request (pyramid.request.Request): The request instance.

        """
        self._request = request
        self._config = request.registry.settings

    def render_html(self):
        pass
