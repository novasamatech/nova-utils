import json
import os
import re
import shutil

# Configuration
CHAINS_FILE = 'chains/v21/chains.json'
OUTPUT_DIR = 'icons/tokens/colored'
REMOVE_UNNECESSARY_ICONS = False


def load_chains_data():
  with open(CHAINS_FILE, 'r') as f:
    return json.load(f)


def save_chains_data(chains_data):
  with open(CHAINS_FILE, 'w') as f:
    json.dump(chains_data, f, indent=2)


def find_file(symbol) -> tuple[str, str]:
  search_symbol = symbol[2:] if symbol.startswith('xc') else symbol

  if search_symbol.startswith('LP '):
    lp_symbol = search_symbol[3:].replace(' ', '')
    return f"{lp_symbol}.svg", f"{lp_symbol}.svg"
  if search_symbol[0].isdigit() or 'WETH' in search_symbol:
    return f"{search_symbol}.svg", f"{search_symbol}.svg"
  if 'RMRK' in search_symbol:
    return "RMRK.svg", "RMRK.svg"

  base_symbol = search_symbol.split('-')[0]
  base_symbol = base_symbol[:-2] if base_symbol.endswith('.s') else base_symbol

  for filename in os.listdir(OUTPUT_DIR):
    if filename.lower() == f"{base_symbol.lower()}.svg":
      return filename, f"{base_symbol}.svg"
    if re.search(rf'\({re.escape(base_symbol)}\)', filename, re.IGNORECASE):
      return filename, f"{base_symbol}.svg"

  return None, None


def update_icons():
  chains_data = load_chains_data()
  unique_tokens = set()
  not_found = []

  for chain in chains_data:
    for asset in chain['assets']:
      process_asset(asset, unique_tokens, not_found)

  save_chains_data(chains_data)
  print_results(not_found)

  if REMOVE_UNNECESSARY_ICONS:
    remove_unreferenced_icons(chains_data)


def process_asset(asset, unique_tokens, not_found):
  symbol = asset['symbol']
  unique_tokens.add(symbol)

  found_file, new_filename = find_file(symbol)
  if found_file:
    update_asset_icon(found_file, new_filename, asset)
  else:
    not_found.append(symbol)


def update_asset_icon(found_file, new_filename, asset):
  old_path = os.path.join(OUTPUT_DIR, found_file)
  new_path = os.path.join(OUTPUT_DIR, new_filename)

  if found_file != new_filename:
    try:
      shutil.move(old_path, new_path)
    except shutil.SameFileError:
      pass

  asset['icon'] = new_filename


def print_results(not_found):
  if not_found:
    print("Symbols not found:")
    for symbol in not_found:
      print(symbol)

  print("Process completed. chains.json has been updated.")

def remove_unreferenced_icons(chains_data):
  referenced_icons = {asset['icon'] for chain in chains_data if 'assets' in chain for asset in chain['assets'] if 'icon' in asset}

  for filename in os.listdir(OUTPUT_DIR):
    if filename not in referenced_icons:
      file_path = os.path.join(OUTPUT_DIR, filename)
      os.remove(file_path)
      print(f"Removed unreferenced file: {filename}")


if __name__ == "__main__":
  os.makedirs(OUTPUT_DIR, exist_ok=True)
  update_icons()
