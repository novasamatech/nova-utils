import json
import os
import re
import shutil

# Load the chains.json file
chains_file = 'chains/v21/chains.json'
with open(chains_file, 'r') as f:
    chains_data = json.load(f)

# Directory to store the renamed SVG files
output_dir = 'icons/tokens/colored'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Function to find a file with a given symbol in its name

def find_file(symbol):
  # Remove 'xc' prefix if present
  search_symbol = symbol[2:] if symbol.startswith('xc') else symbol

  # Handle special cases
  if search_symbol.startswith('LP '):
    lp_symbol = search_symbol[3:].replace(' ', '')
    return f"{lp_symbol}.svg", f"{lp_symbol}.svg"
  if search_symbol[0].isdigit() or 'WETH' in search_symbol:
    return f"{search_symbol}.svg", f"{search_symbol}.svg"

  # Handle RMRK tokens
  if 'RMRK' in search_symbol:
    return "RMRK.svg", "RMRK.svg"

  # Process the symbol
  base_symbol = search_symbol.split('-')[0]
  base_symbol = base_symbol[:-2] if base_symbol.endswith('.s') else base_symbol

  for filename in os.listdir(output_dir):
    if filename.lower() == f"{base_symbol.lower()}.svg":
      return filename, f"{base_symbol}.svg"
    if re.search(rf'\({re.escape(base_symbol)}\)', filename, re.IGNORECASE):
      return filename, f"{base_symbol}.svg"

  return None, None


# Collect all unique tokens and update chains.json
unique_tokens = set()
not_found = []

for chain in chains_data:
  if 'assets' in chain:
    for asset in chain['assets']:
      if 'symbol' in asset:
        symbol = asset['symbol']
        unique_tokens.add(symbol)

        found_file, new_filename = find_file(symbol)
        if found_file:
          old_path = os.path.join(output_dir, found_file)
          new_path = os.path.join(output_dir, new_filename)

          # If the found file is different from the new filename, rename it
          if found_file.lower() != new_filename.lower():
            try:
              shutil.move(old_path, new_path)
            except shutil.SameFileError:
              pass

          # Update the icon path in chains.json
          asset['icon'] = new_filename
        else:
            not_found.append(symbol)

# Print symbols for which files were not found
if not_found:
  print("Symbols not found:")
  for symbol in not_found:
    print(symbol)

# Save the updated chains.json
with open(chains_file, 'w') as f:
  json.dump(chains_data, f, indent=4)

print("Process completed. chains.json has been updated.")
