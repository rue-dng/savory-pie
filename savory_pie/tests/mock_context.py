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

    def set_expected_sha(request, ctx=ctx):
        expected_sha = request.META.get('If-Match')
        if expected_sha:
            ctx.expected_sha = expected_sha

    ctx.set_expected_sha = set_expected_sha
    ctx.expected_sha = None

    return ctx
