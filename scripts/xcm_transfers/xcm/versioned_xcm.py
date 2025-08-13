import types
from typing import List

xcm_version_mode_consts = types.SimpleNamespace()
xcm_version_mode_consts.AlreadyVersioned = "AlreadyVersioned"
xcm_version_mode_consts.DefaultVersion = "DefaultVersion"


class VerionsedXcm:
    unversioned: dict | List
    versioned: dict
    version: int

    @staticmethod
    def default_xcm_version() -> int:
        return 4

    def __init__(self,
                 message: dict | List,
                 message_version: str | int = xcm_version_mode_consts.DefaultVersion,
                 ):
        match message_version:
            case int():
                self._init_from_unversioned(message, version=message_version)
            case xcm_version_mode_consts.AlreadyVersioned:
                self._init_from_versioned(message)
            case xcm_version_mode_consts.DefaultVersion:
                self._init_from_unversioned(message, version=None)
            case _:
                raise Exception(f"Unknown message version mode: {message_version}")

    def _init_from_versioned(self, message: dict):
        if type(message) is not dict:
            raise Exception(f"Already versioned xcm must be a dict with a single version key, got: {message}")

        version_key = next(iter(message))

        self.version = self._parse_version(version_key)
        self.versioned = message
        self.unversioned = message[version_key]

    def _init_from_unversioned(self, message: dict | List, version: int | None):
        if version is None:
            self.version = VerionsedXcm.default_xcm_version()
        else:
            self.version = version

        self.unversioned = message
        self.versioned = {f"V{self.version}": message}

    @staticmethod
    def _parse_version(version_key: str):
        return int(version_key.removeprefix("V"))

    def __str__(self):
        return str(self.versioned)

    def is_v4(self) -> bool:
        return self.version == 4
