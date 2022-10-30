# -*- coding: utf-8 -*-
from pyramid.testing import DummyRequest, testConfig

from mgdm2oereb_service.views.index import Index


def __get_request():
    request = DummyRequest()
    return request


def test_render_html():
    with testConfig():
        result = Index(__get_request()).render_html()
        assert result == {
            'error_msg': None
        }


def test_render_html_with_msg():
    with testConfig():
        request = __get_request()
        request.session['error_msg'] = 'foo'
        result = Index(request).render_html()
        assert result == {
            'error_msg': 'foo'
        }
        assert 'error_msg' not in request.session
