# -*- coding: utf-8 -*-
import redis
from pyramid.httpexceptions import HTTPFound


class Status(object):
    def __init__(self, request):
        """Entry point for index rendering.

        Args:
            request (pyramid.request.Request): The request instance.

        """
        self._request = request
        self._config = request.registry.settings

    def render_html(self):
        # TODO: look for job status in pygeo api and reload
        pass
