from slipway import util


def test_snake_case():
    assert util.snake_case('foo.com/sample:test') == 'foo_com_sample_test'
    assert util.snake_case('/etc/nginx') == 'etc_nginx'
