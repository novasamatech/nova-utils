import re
from abc import ABC, abstractmethod
from typing import List, Any
import json
from utils.work_with_data import get_data_from_file, write_data_to_file


class Command(ABC):

    path: List[str]

    def __init__(self, path: List[str]):
        self.path = path

    @abstractmethod
    def apply_command_to_chain_property(self, chain_property) -> Any:
        pass

    def apply_command(self, chain):
        chain_property = chain
        property_parent = chain

        for idx, segment in enumerate(self.path):
            property_parent = chain_property
            chain_property = chain_property.get(segment, None)

            if idx < len(self.path) - 1 and chain_property is None:
                chain_property = {}
                property_parent[segment] = chain_property

        property_parent[self.path[-1]] = self.apply_command_to_chain_property(chain_property)


class AddCommand(Command):

    element: Any

    def __init__(self, path: List[str], element: Any):
        super().__init__(path)
        self.element = element

    def apply_command_to_chain_property(self, chain_property) -> Any:
        if chain_property is None:
            return [self.element]

        chain_property.append(self.element)
        return chain_property


def parse_command(command_raw: str) -> Command:
    command, arg = command_raw.split(" ")
    command_segments = command.split(".")
    chain_property_path, action = command_segments[:-1], command_segments[-1]

    arg_parsed = json.loads(arg)

    if action == "add":
        return AddCommand(chain_property_path, arg_parsed)
    else:
        raise Exception(f"Unknown command: {command_raw}")



file_names_raw = input("Enter file names you want to modify, separated by space (e.g. v17/chains.json): ")
file_names = file_names_raw.split(" ")

chain_names_raw = input("Enter chain names you want to modify, separated by comma:")
chain_names = re.split(r',\s*', chain_names_raw)


def chains_path(path_suffix: str) -> str:
    return "../chains/" + path_suffix


def load_chains_file(path_suffix):
    return get_data_from_file(chains_path(path_suffix))


def save_chains_file(path_suffix, content):
    raw = json.dumps(content, indent=4)
    write_data_to_file(chains_path(path_suffix), raw)


while True:
    command_raw = input("Enter modify command: ")
    command = parse_command(command_raw)

    for file_name in file_names:
        chains = load_chains_file(file_name)

        for chain_name in chain_names:
            chain = next(c for c in chains if c["name"].casefold() == chain_name.casefold())
            command.apply_command(chain)

        save_chains_file(file_name, chains)

    print("Done")





