# -*- coding: utf-8 -*-
import os
import pytest


@pytest.fixture
def config():
    return {
        'redis': {
            'host': os.environ.get('REDIS_TEST_HOST'),
            'port': 6379,
            'db': 0
        },
        'use_test_data': False
    }
