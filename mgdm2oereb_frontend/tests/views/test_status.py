# -*- coding: utf-8 -*-
import redis
import datetime
from pyramid.httpexceptions import HTTPFound
from pyramid.testing import DummyRequest, testConfig
from pyramid.urldispatch import Route

from mgdm2oereb_service.views.status import Status


class DummyJob(object):
    status = {
        'requests_pending': 1
    }


def __get_request():
    matched_route = Route('status', '/status/{egrid}/{job_id}')
    request = DummyRequest()
    request.matchdict.update({
        'egrid': 'CH123456789000',
        'job_id': 'foo'
    })
    request.matched_route = matched_route
    return request


def test_render_html(config):
    r = redis.Redis(host=config.get('redis').get('host'))
    r.hset('foo', 'status', 'running')
    r.hset('foo', 'timestamp', datetime.datetime.now().isoformat())
    with testConfig(settings=config):
        result = Status(__get_request()).render_html()
        assert result == {
            'status': 'Ihre Anfrage wird bearbeitet.'
        }
        r.delete('foo')


def test_render_html_redirect_delivery(config):
    r = redis.Redis(host=config.get('redis').get('host'))
    r.hset('foo', 'status', 'succeed')
    r.hset('foo', 'timestamp', datetime.datetime.now().isoformat())
    with testConfig(settings=config) as cfg:
        cfg.add_route('delivery', '/get/{egrid}/{job_id}')
        result = Status(__get_request()).render_html()
        assert isinstance(result, HTTPFound)
        r.delete('foo')


def test_render_html_redirect_form(config):
    with testConfig(settings=config) as cfg:
        cfg.add_route('form', '/{egrid}')
        request = __get_request()
        result = Status(request).render_html()
        assert isinstance(result, HTTPFound)
