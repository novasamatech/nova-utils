# Nova Utils

## About
This repo contains static information (logos, links, etc.) to support client apps in Polkadot & Kusama ecosystem (e.g. [Nova Wallet]) to map it to the keys/ids from the network itself.

Note: For better UX in your app it is recommended to
1. prepare UI states & logic when this information cannot be fetched due to gitHub unavailability
2. cache the data to cover part of the issue of 1.

### [List of supported networks](https://github.com/novasamatech/nova-utils/tree/master/chains#supported-networks--assets-data)
### [List of supported dapps](https://github.com/novasamatech/nova-utils/tree/master/dapps#list-of-supported-dapps)

## Modules
#### Crowdloan
Crowdloan JSON objects can contain the following information:
* id (to map the static data)
* Parachain name
* Description
* Logo
* Token
* Website
* Reward rate (DOT/KSM multiplier)

#### Chains
Contains JSON file with networks info: its token (ticker, precision), types, available nodes, account prefix, set of options (is testnet, has crowdloans)

#### Dapps
Contains JSON file with featured DApps

Note: To submit a DApp make sure it's not already in [DApps list](https://github.com/novasamatech/nova-utils/tree/master/dapps#list-of-supported-networks) and if not submit a PR to repository.

#### Icons
Contains the iconography for the different parachains and DApp's.

Note: Icons should be used from trusted sources, however currently icons are not available on the participants' websites, so for convenience, there is /icons folder.

[Nova Wallet]: https://t.me/novawallet

### Submitting Contributions

- Fork the repository and create a new branch for your contribution.
- Initialize repository by: `make init`
- Commit your changes with a descriptive commit message.
- Push your branch to your forked repository.
- Submit a pull request detailing your changes and explaining why they should be merged.

## License
Nova utils is available under the Apache 2.0 license. See the LICENSE file for more info.
© Novasama Technologies GmbH 2023