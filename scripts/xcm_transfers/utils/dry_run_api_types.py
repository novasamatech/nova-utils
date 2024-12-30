def dry_run_api_types(runtime_types_prefix: str | None) -> dict | None:
    if runtime_types_prefix is None:
        return None

    return {
        "runtime_api": {
            "DryRunApi": {
                "methods": {
                    "dry_run_call": {
                        "description": "Dry run runtime call",
                        "params": [
                            {
                                "name": "origin_caller",
                                "type": f"{runtime_types_prefix}::OriginCaller"
                            },
                            {
                                "name": "call",
                                "type": "GenericCall"
                            }
                        ],
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
                                "staging_xcm::v4::traits::Outcome"
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
