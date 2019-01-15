from .. import utils


def test_shrink_str():
    assert utils.shrink_str('foo') == 'foo'
    assert utils.shrink_str('foo', max_length=2) == 'fo…'
