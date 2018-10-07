from datetime import datetime
import requests

EXPIRE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class CloudFilesSession(requests.Session):
    _rackspace_credentials = None
    _rackspace_region = None
    _base_url = None
    _expires = None

    def __init__(self, username, apikey, region):
        self._rackspace_credentials = {"username": username, "apiKey": apikey}
        self._rackspace_region = region
        super().__init__()
        self.update()

    def request(self, method, url, *args, **kwargs):
        return super().request(method, f"{self._base_url}/{url}", *args, **kwargs)

    def update(self):
        response = requests.post(
            "https://identity.api.rackspacecloud.com/v2.0/tokens",
            json={"auth": {"RAX-KSKEY:apiKeyCredentials": self._rackspace_credentials}},
        )
        response.raise_for_status()
        data = response.json()
        access = data["access"]
        token = access["token"]
        token_id = token["id"]

        self._expires = datetime.strptime(token['expires'], EXPIRE_FORMAT)

        endpoints_map = {
            cat["type"]: cat["endpoints"] for cat in access["serviceCatalog"]
        }
        endpoints = endpoints_map["object-store"]
        region_map = {
            endpoint["region"]: endpoint["publicURL"] for endpoint in endpoints
        }
        public_url = region_map[self._rackspace_region]

        self._base_url = public_url
        self.headers["X-Auth-Token"] = token_id
