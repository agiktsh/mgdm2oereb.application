# -*- coding: utf-8 -*-
import json

import pytest
from base64 import b64encode
from json import dumps

import redis
from pyramid.httpexceptions import HTTPFound
from pyramid.testing import testConfig, DummyRequest
from pyramid.urldispatch import Route

from mgdm2oereb_service.views.delivery import Delivery


terris_result = {
    'real_estate': {
        'number': '1234',
        'municipality': 'Testwil',
        'egrid': 'CH123456789000'
    },
    'ownerships': [
        {
            'type': 'address',
            'text': 'foo'
        }
    ]
}


class DummyJob(object):

    errors = []

    def __init__(self, result):
        self._result = result

    def get_result(self):
        return self._result


def __get_request():
    matched_route = Route('delivery', '/get/{egrid}/{job_id}')
    request = DummyRequest()
    request.matchdict.update({'job_id': 'abcdef'})
    request.matchdict.update({'egrid': 'CH123456789000'})
    request.matched_route = matched_route
    return request


@pytest.mark.parametrize('use_test_data', [
    (False,),
    (True,)
])
def test_render_html(use_test_data, config):
    config.update({
        'use_test_data': use_test_data
    })
    r = redis.Redis(host=config.get('redis').get('host'))
    r.hset('abcdef', 'status', 'succeed')
    r.hset('abcdef', 'duration', 1.0)
    r.hset('abcdef', 'result', json.dumps(terris_result))
    with testConfig(settings=config):
        request = __get_request()
        delivery = Delivery(request)
        result = delivery.render_html()
        assert result == {
            'real_estate': terris_result.get('real_estate'),
            'ownerships': terris_result.get('ownerships'),
            'debug': False,
            'print_data': delivery._get_print_data(terris_result),
            'use_test_data': use_test_data
        }
        r.delete('abcdef')


def test_render_html_redirect(config):
    with testConfig(settings=config) as cfg:
        cfg.add_route('form', '/{egrid}')
        request = __get_request()
        del request.matchdict['job_id']
        result = Delivery(request).render_html()
        assert isinstance(result, HTTPFound)


def test_get_print_data(config):
    data = {
        'real_estate': {
            'number': '1234',
            'municipality': 'Testwil',
            'egrid': 'CH123456789000'
        },
        'ownerships': []
    }
    expected_data = {
        'parcel_number': data.get('real_estate').get('number'),
        'egrid': data.get('real_estate').get('egrid'),
        'municipality': data.get('real_estate').get('municipality'),
        'parcel_statistic_link': 'https://geoview.bl.ch/grundstueck/?egrid={0}'.format(
            data.get('real_estate').get('egrid')
        ),
        'ownership': '    '
    }
    with testConfig(settings=config):
        result = Delivery._get_print_data(data)
        assert result == b64encode(dumps(expected_data).encode('utf-8')).decode('utf-8')
