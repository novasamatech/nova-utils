from .substrate_interface import create_connection_by_url
from .metadata_interaction import get_properties

from substrateinterface import SubstrateInterface


class Chain():
    substrate: SubstrateInterface

    def __init__(self, arg):
        self.chainId = arg.get("chainId")
        self.parentId = arg.get("parentId")
        self.name = arg.get("name")
        self.assets = arg.get("assets")
        self.nodes = arg.get("nodes")
        self.explorers = arg.get("explorers")
        self.addressPrefix = arg.get("addressPrefix")
        self.externalApi = arg.get("externalApi")
        self.substrate = None
        self.properties = None

    def create_connection(self) -> SubstrateInterface:
        for node in self.nodes:
            try:
                self.substrate = create_connection_by_url(node.get('url'))
                return self.substrate
                # if self.substrate.websocket.connected is True:
                #     return self.substrate
                # print(f"Can't connect to endpoint {node.get('url')} for the {self.name}")
            except:
                print("Can't connect to that node")
                continue

        print("Can't connect to all nodes of network", self.name)


    def close_substrate_connection(self):
        self.substrate.close()


    def init_properties(self):
        if (self.properties):
                return self.substrate
        self.properties = get_properties(self.substrate)