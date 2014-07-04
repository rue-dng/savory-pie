from django.http import HttpRequest


class DjangoSavoryRequestProxy(HttpRequest):

    def __init__(self, body_stream, user):
        self.body_stream = body_stream
        self.user = user
        super(DjangoSavoryRequestProxy, self).__init__()

    def read(self, *args, **kwargs):
        return self.body_stream.read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        return self.body_stream.readline(*args, **kwargs)

    def xreadlines(self):
        while True:
            buf = self.readline()
            if not buf:
                break
            yield buf

    def readlines(self):
        return list(iter(self))

    __iter__ = xreadlines
