# -*- coding: utf-8 -*-
import json
import logging
import re
import datetime
from uuid import uuid4

import redis

from pyramid.httpexceptions import HTTPFound


log = logging.getLogger('mgdm2oereb_frontend')


class Form(object):
    def __init__(self, request):
        """Entry point for index rendering.

        Args:
            request (pyramid.request.Request): The request instance.

        """
        self._request = request
        self._config = request.registry.settings

    def upload(self):
        if self._request.method == 'POST':
            # TODO: start job in pygeoapi and pass over to status page
            pass
        pass
