
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

## Our networks list
|        Network         |                       Assets                       |     Explorers     |                                      History                                       |                         Staking                         |
| ---------------------- | -------------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Polkadot               | DOT                                                | Subscan,Polkascan | [subquery](https://nova-polkadot.gapi.subquery.network)                            | [subquery](https://nova-polkadot.gapi.subquery.network) |
| Kusama                 | KSM                                                | Subscan,Polkascan | [subquery](https://nova-kusama.gapi.subquery.network)                              | [subquery](https://nova-kusama.gapi.subquery.network)   |
| Westend                | WND                                                | Subscan           | [subquery](https://nova-westend.gapi.subquery.network)                             | [subquery](https://nova-westend.gapi.subquery.network)  |
| Statemine              | KSM,RMRK,CHAOS,CHRWNA,SHIBATALES,BILLCOIN,ARIS     | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-statemine)      |  -                                                      |
| Karura                 | KAR,kUSD,KSM,RMRK,BNC,LKSM,PHA,KINT,kBTC,TAI,vsKSM | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-karura)         |  -                                                      |
| Moonbeam               | GLMR                                               | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-moonbeam)       |  -                                                      |
| Moonriver              | MOVR,xcRMRK,xcKSM                                  | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-moonriver)      |  -                                                      |
| Shiden                 | SDN                                                | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-shiden)         |  -                                                      |
| Bifrost                | BNC,KSM,RMRK,ZLK,KAR,kUSD,vsKSM                    | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-bifrost)        |  -                                                      |
| Basilisk               | BSX                                                |  -                |  -                                                                                 |  -                                                      |
| Altair                 | AIR                                                |  -                | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-altair)         |  -                                                      |
| Parallel Heiko         | HKO                                                | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-parallel-heiko) |  -                                                      |
| Edgeware               | EDG                                                | Subscan           |  -                                                                                 |  -                                                      |
| Khala                  | PHA                                                | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-khala)          |  -                                                      |
| KILT Spiritnet         | KILT                                               | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-kilt)           |  -                                                      |
| Calamari               | KMA                                                | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-calamari)       |  -                                                      |
| QUARTZ                 | QTZ                                                |  -                | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-quartz)         |  -                                                      |
| Bit.Country Pioneer    | NEER                                               |  -                | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-bit-country)    |  -                                                      |
| Acala                  | ACA,LDOT,aUSD,DOT,LCDOT                            | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-acala)          |  -                                                      |
| Astar                  | ASTR                                               | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-astar)          |  -                                                      |
| Parallel               | PARA                                               | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-parallel)       |  -                                                      |
| Clover                 | CLV                                                | Subscan           | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-clover)         |  -                                                      |
| Statemint              | DOT                                                |  -                | [subquery](https://api.subquery.network/sq/nova-wallet/nova-wallet-statemint)      |  -                                                      |
| Subsocial (Standalone) | SUB                                                |  -                |  -                                                                                 |  -                                                      |
| Robonomics             | XRT                                                |  -                |  -                                                                                 |  -                                                      |
| Encointer              | KSM                                                |  -                |  -                                                                                 |  -                                                      |
| Kintsugi               | KINT,kBTC,KSM                                      |  -                |  -                                                                                 |  -                                                      |
| Picasso                | PICA                                               |  -                |  -                                                                                 |  -                                                      |
| Zeitgeist              | ZTG                                                |  -                |  -                                                                                 |  -                                                      |
