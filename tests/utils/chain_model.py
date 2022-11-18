from scripts.utils.network_interaction import create_connection_by_url
from scripts.create_type_file import get_properties


class Chain():

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

    def create_connection(self):
        for node in self.nodes:
            if (self.substrate):
                return self.substrate
            try:
                self.substrate = create_connection_by_url(node.get('url'))
                return self.substrate
            except:
                print("Can't connect to that node")
                continue

        raise TimeoutError("Can't connect to all nodes of network", self.name)


    def init_properties(self):
        if (self.properties):
                return self.substrate
        self.properties = get_properties(self.substrate)