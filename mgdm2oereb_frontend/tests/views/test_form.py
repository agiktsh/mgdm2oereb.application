# -*- coding: utf-8 -*-
import redis
from pyramid.httpexceptions import HTTPFound
from pyramid.testing import DummyRequest, testConfig
from pyramid.urldispatch import Route

from mgdm2oereb_service.views.form import Form


def __get_request():
    matched_route = Route('form', '/{egrid}')
    request = DummyRequest()
    request.matchdict.update({'egrid': 'CH123456789000'})
    request.session.update({'captcha': 'abc123'})
    request.POST.update({'captcha': 'abc123'})
    request.matched_route = matched_route
    return request


class DummyForm(Form):
    def _create_job(self):
        return '1'


def test_render_html(config):
    with testConfig(settings=config):
        request = __get_request()
        result = Form(request).render_html()
        assert 'captcha_invalid' not in request.session
        assert not result['captcha_invalid']


def test_render_html_invalid_egrid(config):
    with testConfig(settings=config) as cfg:
        cfg.add_route('index', '/')
        request = __get_request()
        request.matchdict.update({'egrid': 'foo'})
        result = Form(request).render_html()
        assert isinstance(result, HTTPFound)
        assert result.location == 'http://example.com/'
        assert request.session.get('error_msg') == u'"{0}" ist kein gültiger EGRID.'.format(
            request.matchdict.get('egrid')
        )


def test_render_html_invalid_captcha(config):
    with testConfig(settings=config):
        request = __get_request()
        request.session['captcha_invalid'] = True
        result = Form(request).render_html()
        assert 'captcha_invalid' not in request.session
        assert result['captcha_invalid']


def test_validate_succeed(config):
    with testConfig(settings=config) as cfg:
        cfg.add_route('status', '/status/{egrid}/{job_id}')
        result = DummyForm(__get_request()).validate()
        assert isinstance(result, HTTPFound)
        assert result.location == 'http://example.com/status/CH123456789000/1'


def test_validate_failed(config):
    with testConfig(settings=config) as cfg:
        cfg.add_route('form', '/{egrid}')
        request = __get_request()
        request.POST.update({
            'captcha': 'cde456'
        })
        result = Form(request).validate()
        assert isinstance(result, HTTPFound)
        assert result.location == 'http://example.com/CH123456789000'


def test_create_job(config):
    r = redis.Redis(host=config.get('redis').get('host'))
    with testConfig(settings=config):
        request = __get_request()
        uuid = Form(request)._create_job()
        assert r.hget(uuid, 'status') == b'queued'
        r.delete(uuid)


def test_get_proxy_config_empty(config):
    with testConfig(settings=config):
        request = __get_request()
        result = Form(request)._get_proxy_config()
        assert result == {}


def test_get_proxy_config(config):
    with testConfig(settings=config):
        request = __get_request()
        request.registry.settings.update({
            'proxy': {
                'http': 'foo',
                'https': 'bar'
            }
        })
        result = Form(request)._get_proxy_config()
        assert result == {
            'http': 'foo',
            'https': 'bar'
        }
