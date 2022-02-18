
# Nova Utils

## About
This repo contains static information (logos, links, etc) to support client apps in Polkadot & Kusama ecosystem (e.g. [Nova Wallet]) to map it to the keys/ids from the network itself.

Note: For better UX in your app its recommended to
1. prepare UI states & logic when this information cannot be fetched due to github unavailability
2. cache the data to cover part of the issue of 1.

## Modules
#### Crowdloan
Crowdloans can be saturated with the following information:
* id (to map the static data)
* Parachain name
* Description
* Logo
* Token
* Website
* Reward rate (KSM multiplier)

#### Chains
Contains JSON file with networks info: its token (ticker, precision), types, available nodes, account prefix, set of options (is testnet, has crowdloans)

#### Icons
Group of icons to saturate Nova Wallet

Note: Icons should be used from trusted sources, however currently icons are not available on the participants' websites, so for convenience, there is /icons folder.

### [Our networks list](https://github.com/stepanLav/nova-utils/tree/master/chains/README.md)
