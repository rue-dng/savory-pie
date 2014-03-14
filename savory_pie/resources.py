#protocol Params:
#   def get(key, default=None)
#   def get_as(key, type, default=None)
#   def get_list(key)
#   def get_list_of(key, type)


class EmptyParams(object):
    def get(self, key, default=None):
        return default

    def get_as(self, key, type, default=None):
        return default

    def get_list(self, key):
        return []

    def get_list_of(self, key, type):
        return []

    def keys(self):
        return []


class Resource(object):
    """
    Base object for defining resources.
    """
    #: Internal path (from root of the resource tree to this Resource).  If not
    #: set, this is auto-filled during Resource traversal; however, if you wish
    #: for a Resource to always be addressable, resource_path should be set at
    #: construction.
    resource_path = None

    validators = []

    @property
    def allowed_methods(self):
        """
        defaults to set of available methods based on
        presence of the optional methods - get, post, put, etc.

        Can be overridden with a static set or dynamic property to
        create access controls.
        """
        allowed_methods = set()

        for http_method in ['GET', 'POST', 'PUT', 'DELETE']:
            obj_method = http_method.lower()
            try:
                getattr(self, obj_method)
                allowed_methods.add(http_method)
            except AttributeError:
                pass

        return allowed_methods

    # def get(self, ctx, params):
        """
        Optional method that is called during a GET request.

        get is provided an APIContext and an optional set of kwargs that include the
        query string params.

        Returns a dict of data to be serialized to the requested format.
        """

    # def post(self, ctx, dict):
        """
        Optional method that is called during a POST request.

        post is provided with a dict representing the deserialized representation of
        the body content.

        Returns a new Resource
        """

    # def put(self, ctx, dict, save):
        """
        Optional method that is called during a PUT request.

        put is provided with a dict representing the deserialized representation of
        the body content.
        """

    # def delete(self, ctx):
        """
        Optional method that is called during a DELETE request.
        """

    def get_child_resource(self, ctx, path_fragment):
        return None


class APIResource(Resource):
    def __init__(self, resource_path=''):
        self.resource_path = resource_path
        self._child_resources = dict()

    def register(self, resource):
        """
        Register a resource into the API.
        """
        leaf = resource.resource_path
        if '/' in resource.resource_path:
            n = resource.resource_path.index('/')
            leaf = resource.resource_path[n + 1:]

        self._child_resources[leaf] = resource
        return self

    def register_class(self, resource_class):
        """
        Register a resource class into the API.  The constructed Resource
        must have a first-level resource_path set after construction.
        """
        return self.register(resource_class())

    def get_child_resource(self, ctx, path_fragment):
        return self._child_resources.get(path_fragment, None)
