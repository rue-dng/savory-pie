from savory_pie.formatters import JSONFormatter

from mock import Mock

def mock_context():
    ctx = Mock(name='context', spec=[])
    ctx.formatter = JSONFormatter()
    ctx.build_resource_uri = lambda resource: 'uri://' + resource.resource_path
    return ctx