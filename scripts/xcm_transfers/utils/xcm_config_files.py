import dataclasses


@dataclasses.dataclass
class XCMConfigFiles(object):

    chains: str

    # Currently used legacy config. Subject to modifications (e.g. cleanup) by the scripts
    xcm_legacy_config: str

    # Stable version of the legacy config that can be used as a source to construct `xcm_legacy_config` by remaing
    # directions present in `xcm_dynamic_config`
    xcm_stable_legacy_config: str

    xcm_dynamic_config: str

    xcm_additional_data: str

    general_config: str
