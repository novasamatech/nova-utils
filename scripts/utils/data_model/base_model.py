import json


class BaseObject:

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          indent=2)


class BaseParameters(BaseObject):
    asset: str
    source_network: str
    destination_network: str

    def __init__(self, **kwargs):
        for k in kwargs.keys():
            self.__setattr__(k, kwargs[k])
