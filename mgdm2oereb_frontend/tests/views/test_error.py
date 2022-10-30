# -*- coding: utf-8 -*-
import redis

from pyramid.httpexceptions import HTTPFound
from pyramid.testing import DummyRequest, testConfig
from pyramid.urldispatch import Route

from mgdm2oereb_service.views.error import Error


class DummyJob(object):
    errors = ['bar']


def __get_request():
    matched_route = Route('error', '/error/{egrid}/{job_id}')
    request = DummyRequest()
    request.matchdict.update({
        'egrid': 'CH123456789000',
        'job_id': 'foo'
    })
    request.matched_route = matched_route
    return request


def test_render_html(config):
    r = redis.Redis(host=config.get('redis').get('host'))
    r.hset('foo', 'status', 'failed')
    r.hset('foo', 'error', 'bar')
    with testConfig(settings=config):
        request = __get_request()
        result = Error(request).render_html()
        assert result == {
            'error': b'bar',
            'debug': False
        }
        r.delete('foo')


def test_render_html_redirect(config):
    with testConfig(settings=config) as cfg:
        cfg.add_route('form', '/{egrid}')
        request = __get_request()
        result = Error(request).render_html()
        assert isinstance(result, HTTPFound)
