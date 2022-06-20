import pytest

from cf_config.config import CloudConfig


@pytest.fixture()
def test_config():
    all_env = {
        'fallback': 'all'
    }

    dev_env = {
        'dev': 'dev'
    }

    config = CloudConfig('test')

    config.update_dev(dev_env)

    config.update_all(all_env)

    return config


class TestConfig:

    def test_simple_found(self, test_config):
        assert 'dev' == test_config['dev:dev']

    def test_simple_fallback(self, test_config):
        assert 'all' == test_config['dev:fallback']

    def test_simple_not_found(self, test_config):
        assert None is test_config['test:test']



