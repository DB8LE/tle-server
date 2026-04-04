import tomllib
from collections import defaultdict
from typing import Dict, List, Tuple

def read_groups(file_path: str) -> Tuple[Dict[str, List[int]], Dict[str, List[str]]]:
    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    group_ids = {}
    source_groups = defaultdict(list)
    for name, config in data.items():
        if "norad_ids" in config.keys():
            group_ids[name] = config["norad_ids"]

        if "inherit_sources" in config.keys():
            for source in config["inherit_sources"]:
                source_groups[source].append(name)

    return group_ids, source_groups
