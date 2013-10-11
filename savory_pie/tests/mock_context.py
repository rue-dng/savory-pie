import contextlib

from savory_pie.formatters import JSONFormatter

from mock import Mock


def mock_context():
    @contextlib.contextmanager
    def target(*args):
        ctx.push(*args)
        yield
        ctx.pop()

    ctx = Mock(name='context', spec=['push', 'pop', 'peek'])
    ctx.formatter = JSONFormatter()
    ctx.build_resource_uri = lambda resource: 'uri://' + resource.resource_path
    ctx.target = target
    return ctx
