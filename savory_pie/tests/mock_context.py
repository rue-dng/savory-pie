import contextlib

from savory_pie.formatters import JSONFormatter

from mock import Mock

@contextlib.contextmanager
def target(*args):
    yield

def mock_context():
    ctx = Mock(name='context', spec=[])
    ctx.formatter = JSONFormatter()
    ctx.build_resource_uri = lambda resource: 'uri://' + resource.resource_path
    ctx.target = target
    return ctx
