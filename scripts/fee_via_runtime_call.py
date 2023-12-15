import json
from typing import Set

from os import listdir
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file

v17_path = "../chains/v17/chains_dev.json"

v16_chains = get_data_from_file("../chains/v16/chains_dev.json")
v17_chains = get_data_from_file(v17_path)


path = "../chains/v2/types"
files = [f for f in listdir(path)]


def find_type_files_containing(searched_key: str) -> Set:
    found_files = []

    for file in files:
        file_data = get_data_from_file(path + "/" + file)

        for key in file_data["types"]:
            if key == searched_key:
                found_files.append("https://raw.githubusercontent.com/novasamatech/nova-utils/master/chains/v2/types/" + file)

    return found_files


found_files = find_type_files_containing("RuntimeDispatchInfo")
print(len(found_files))

modified_chains = 0

for v17_chain in v17_chains:
    v16_chain = next((x for x in v16_chains if x["chainId"] == v17_chain["chainId"]), None)

    if v16_chain is None or "types" not in v16_chain:
        continue

    if not v16_chain["types"]["url"] in found_files:
        continue

    current_additional = v17_chain.get("additional", {})
    current_additional["feeViewRuntimeCall"] = True
    v17_chain["additional"] = current_additional
    found_files.remove(v16_chain["types"]["url"])
    modified_chains+=1

print(f"Still remaining: {found_files}")
print(f"Modified: {modified_chains}")

write_data_to_file(v17_path, json.dumps(v17_chains, indent=4))
