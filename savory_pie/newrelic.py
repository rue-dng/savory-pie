import functools


try:
    import newrelic.agent as agent

    def set_transaction_name(func):
        @functools.wraps
        def inner(request, resource_path):
            agent.set_transaction_name(
                resource_path,
                'Python/WebFramework/Controller'
            )
            return func(request, resource_path)
        return inner

except ImportError:
    def set_transaction_name(func):
        return func
