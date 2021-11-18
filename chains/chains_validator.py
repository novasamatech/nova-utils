from functools import reduce
from typing import Callable, List

import yaml
import json
from urllib.parse import unquote, urlparse
from pathlib import PurePosixPath
import os.path
import os


class Types:

    def __init__(self, types_config):
        local_path = Types.__remote_url_to_local(types_config["url"])

        with open(local_path) as fin:
            self.types_dict = json.load(fin)

        self.is_v14 = Types.__is_v14(self.types_dict)
        self.overrides_common = types_config.get("overridesCommon", False)

    @staticmethod
    def __is_v14(types_dict):
        # ParaId types is only has to be defined for v14 types
        return "ParaId" in types_dict["types"].keys()

    @staticmethod
    def __remote_url_to_local(url: str):
        path_parts = PurePosixPath(unquote(urlparse(url).path)).parts

        after_chains_index = path_parts.index("chains")

        # dirname = os.path.dirname(__file__)

        relative_path_parts = path_parts[(after_chains_index + 1):]
        local_path = os.path.join("", *relative_path_parts)

        return local_path

    @staticmethod
    def parse_from(chain_config):
        types_config = chain_config.get("types")

        return None if types_config is None else Types(types_config)


class Chain:

    def __init__(self, chain_config):
        self.config = chain_config
        self.types = Types.parse_from(chain_config)
        self.name = chain_config["name"]


def v14_types_should_override_common(chain: Chain) -> List[str]:
    if chain.types is not None and chain.types.is_v14 and not chain.types.overrides_common:
        return ["v14 types should have overrideCommon set to True"]
    else:
        return []


ALL_RULES: List[Callable[[Chain], List[str]]] = [
    v14_types_should_override_common
]

with open("chains_validator.yaml") as fin:
    config = yaml.safe_load(fin)

found_problems = False

for chain_file in config["chain_files"]:
    with open(chain_file) as fin:
        all_chains_config = json.load(fin)

    for chain_config in all_chains_config:
        try:
            chain = Chain(chain_config)

            chain_problems = reduce(lambda acc, rule: acc + rule(chain), ALL_RULES, [])
        except Exception as e:
            chain_problems = [str(e)]

        for problem in chain_problems:
            print(f"{chain_file}->{chain_config['name']}: {problem}")

        if len(chain_problems) > 0:
            found_problems = True

if found_problems:
    exit(1)
