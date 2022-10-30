# -*- coding: utf-8 -*-
from pyramid.testing import testConfig, DummyRequest

from mgdm2oereb_service.views.proxy import Print


def test_print_init():
    settings = {
        'print_url': 'http://example.com'
    }
    with testConfig(settings=settings):
        proxy = Print(DummyRequest())
        assert isinstance(proxy._request, DummyRequest)
        assert proxy._print_url == 'http://example.com'
        assert proxy._file_format == 'pdf'
        assert proxy._filename.endswith('_Eigentumsauskunft.{0}'.format(proxy._file_format))
