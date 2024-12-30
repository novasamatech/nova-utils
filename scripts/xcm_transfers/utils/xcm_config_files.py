import dataclasses


@dataclasses.dataclass
class XCMConfigFiles(object):

    chains: str

    xcm_legacy_config: str

    xcm_dynamic_config: str

    xcm_additional_data: str
