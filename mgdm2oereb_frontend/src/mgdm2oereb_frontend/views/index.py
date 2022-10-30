# -*- coding: utf-8 -*-


class Index(object):
    def __init__(self, request):
        """Entry point for index rendering.

        Args:
            request (pyramid.request.Request): The request instance.

        """
        self._request = request
        self._config = request.registry.settings

    def render_html(self):
        error_msg = None
        return dict(error_msg=error_msg)
