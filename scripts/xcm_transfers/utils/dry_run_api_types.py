from typing import List

dry_run_v1 = 1
dry_run_v2 = 2


def dry_run_api_types(
        runtime_types_prefix: str | None,
        dry_run_version: int,
        xcm_outcome_type: str
) -> dict | None:
    if runtime_types_prefix is None:
        return None

    return {
        "runtime_api": {
            "DryRunApi": {
                "methods": {
                    "dry_run_call": {
                        "description": "Dry run runtime call",
                        "params": determine_dry_run_call_args(runtime_types_prefix, dry_run_version),
                        "type": "CallDryRunEffectsResult"
                    },
                    "dry_run_xcm": {
                        "description": "Dry run xcm program",
                        "params": [
                            {
                                "name": "origin_location",
                                "type": "xcm::VersionedLocation"
                            },
                            {
                                "name": "xcm",
                                "type": "xcm::VersionedXcm"
                            }
                        ],
                        "type": "XcmDryRunEffectsResult"
                    },
                },
                "types": {
                    "CallDryRunEffectsResult": {
                        "type": "enum",
                        "type_mapping": [
                            [
                                "Ok",
                                "CallDryRunEffects"
                            ],
                            [
                                "Error",
                                "DryRunEffectsResultErr"
                            ]
                        ]
                    },
                    "DryRunEffectsResultErr": {
                        "type": "enum",
                        "value_list": [
                            "Unimplemented",
                            "VersionedConversionFailed"
                        ]
                    },
                    "CallDryRunEffects": {
                        "type": "struct",
                        "type_mapping": [
                            [
                                "execution_result",
                                "CallDryRunExecutionResult"
                            ],
                            [
                                "emitted_events",
                                f"Vec<{runtime_types_prefix}::RuntimeEvent>"
                            ],
                            [
                                "local_xcm",
                                "Option<xcm::VersionedXcm>"
                            ],
                            [
                                "forwarded_xcms",
                                "Vec<(xcm::VersionedLocation, Vec<xcm::VersionedXcm>)>"
                            ]
                        ]
                    },
                    "CallDryRunExecutionResult": {
                        "type": "enum",
                        "type_mapping": [
                            [
                                "Ok",
                                "DispatchPostInfo"
                            ],
                            [
                                "Error",
                                "DispatchErrorWithPostInfo"
                            ]
                        ]
                    },
                    "XcmDryRunEffects": {
                        "type": "struct",
                        "type_mapping": [
                            [
                                "execution_result",
                                xcm_outcome_type
                            ],
                            [
                                "emitted_events",
                                f"Vec<{runtime_types_prefix}::RuntimeEvent>"
                            ],
                            [
                                "forwarded_xcms",
                                "Vec<(xcm::VersionedLocation, Vec<xcm::VersionedXcm>)>"
                            ]
                        ]
                    },
                    "XcmDryRunEffectsResult": {
                        "type": "enum",
                        "type_mapping": [
                            [
                                "Ok",
                                "XcmDryRunEffects"
                            ],
                            [
                                "Error",
                                "DryRunEffectsResultErr"
                            ]
                        ]
                    },
                    "DispatchErrorWithPostInfo": {
                        "type": "struct",
                        "type_mapping": [
                            [
                                "post_info",
                                "DispatchPostInfo"
                            ],
                            [
                                "error",
                                "sp_runtime::DispatchError"
                            ],
                        ]
                    },
                    "DispatchPostInfo": {
                        "type": "struct",
                        "type_mapping": [
                            [
                                "actual_weight",
                                "Option<Weight>"
                            ],
                            [
                                "pays_fee",
                                "frame_support::dispatch::Pays"
                            ],
                        ]
                    }
                }
            },
        }
    }

def determine_dry_run_call_args(runtime_types_prefix: str | None, dry_run_version: int) -> List:
    origin_caller = {
        "name": "origin_caller",
        "type": f"{runtime_types_prefix}::OriginCaller"
    }
    call = {
        "name": "call",
        "type": "GenericCall"
    }
    xcm_versions_result = {
        "name": "result_xcms_version",
        "type": "u32"
    }

    match dry_run_version:
        case 1:
            return [origin_caller, call]
        case _:
            return [origin_caller, call, xcm_versions_result]