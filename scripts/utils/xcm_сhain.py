class XcmChain:
    chainID = str
    chainName = str
    assets = [{
        "asset": str,
        "destination": [str]
    }]

    def __init__(self, xcm_chain, chains):
        self.chainID = xcm_chain.get('chainId')
        self.chainName = [chain.get('name') for chain in chains if chain.get(
            'chainId') == self.chainID][0]
        self.assets = self.__fill_assets_list__(xcm_chain, chains)

    def __fill_assets_list__(self, xcm_chain, chains):
        assets = []
        destination = []
        for asset in xcm_chain.get('assets'):
            for dest in asset.get('xcmTransfers'):
                dest_chain_id = dest.get('destination').get('chainId')
                destination.append([chain.get('name') for chain in chains if chain.get(
                    'chainId') == dest_chain_id][0])
            current_asset = {
                "asset": asset.get('assetLocation'),
                "destination": destination
            }
            assets.append(current_asset)
            destination = []
        return assets
