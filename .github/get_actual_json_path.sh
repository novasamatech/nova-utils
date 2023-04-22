#!/bin/bash
SCRIPT_PATH=$(dirname "$0")
MAIN_DIRECTORY=${SCRIPT_PATH%/*}

# Retrieve the folder names and extract the version numbers
folders=($(ls -1 ${MAIN_DIRECTORY}/../$1))
version_numbers=()
for folder in "${folders[@]}"; do
  # Extract the version number by removing the "v" prefix and any non-numeric characters
  version_number=$(echo ${folder#v} | tr -dc '[:digit:]')
  # Append the extracted version number to the array
  version_numbers+=($version_number)
done

# Sort the version numbers in descending order
sorted_version_numbers=($(printf '%s\n' "${version_numbers[@]}" | sort -rn))

# Retrieve the latest version folder
latest_version_number=${sorted_version_numbers[0]}
latest_version_folder="v${latest_version_number}"

echo $latest_version_folder
