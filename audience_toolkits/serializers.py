from urllib.parse import urlparse

from rest_framework.relations import HyperlinkedIdentityField


class HyperlinkedRetrieveIdentityField(HyperlinkedIdentityField):
    def get_url(self, *args):
        url = super().get_url(*args)
        parsed = urlparse(url)
        return parsed.path
