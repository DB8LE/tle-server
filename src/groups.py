import logging
import tomllib
from collections import defaultdict
from typing import Dict, List, Tuple

def read_groups(file_path: str) -> Tuple[Dict[str, List[int]], Dict[str, List[str]]]:
    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    # Parse copy_groups attribute
    for name, config in data.items():
        if "copy_groups" in config.keys():
            for copy_name in config["copy_groups"]:
                copy_config = data[copy_name]
                if "norad_ids" in copy_config.keys():
                    config["norad_ids"].extend(copy_config["norad_ids"])
                    config["norad_ids"] = list(set(config["norad_ids"])) # Deduplicate
                if "inherit_sources" in copy_config.keys():
                    config["inherit_sources"].extend(copy_config["inherit_sources"])
                    config["inherit_sources"] = list(set(config["inherit_sources"])) # Deduplicate

    # Parse other attributes
    group_ids = defaultdict(list)
    source_groups = defaultdict(list)
    for name, config in data.items():
        if "norad_ids" in config.keys():
            group_ids[name] = config["norad_ids"]

        if "inherit_sources" in config.keys():
            for source in config["inherit_sources"]:
                source_groups[source].append(name)

    return dict(group_ids), dict(source_groups)
