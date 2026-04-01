import tomllib
from typing import Dict, List


def read_groups(file_path: str) -> Dict[str, List[int]]:
    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    out = {}
    for name, config in data.items():
        out[name] = config["norad_ids"]

    return out
