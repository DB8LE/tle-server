import json
import logging
import requests
import tomllib
import traceback
from datetime import datetime, timezone
from typing import List, Literal, Optional
from .element import Element


class Source:
    def __init__(self, name: str, data_type: Literal["json"], url: str):
        self.name = name
        self.data_type = data_type
        self.url = url

    def fetch(self) -> Optional[List[Element]]:
        logging.debug(
            f"Attempting to fetch elements with type {self.data_type} from {self.url}"
        )
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            data = response.text
        except Exception as e:
            logging.error(f"Exception while getting TLE data from {self.url}: {e}")
            return None

        try:
            download_time = datetime.now(timezone.utc)
            if self.data_type == "json":
                data = json.loads(data)
                if type(data) is list:
                    out = []
                    for tle in data:
                        out.append(Element.from_json(tle, self.name, download_time))
                    return out
                elif type(data) is dict:
                    return [Element.from_json(data, self.name, download_time)]
                else:
                    logging.error(f"Source {self.name} returned invalid json type")
                    return None
            elif self.data_type == "tle":
                lines = data.splitlines()

                out = []
                skip = False
                name_line = ""
                for i, line in enumerate(lines):
                    if skip:
                        skip = False
                        continue

                    # Skip empty lines
                    if len(line.strip()) == 0:
                        name_line = ""
                        continue

                    # Length of 69 is a data line
                    if len(line) == 69:
                        line1 = line.strip()
                        line2 = lines[i + 1].strip()
                        skip = True

                        tle_lines = [line1, line2]
                        if name_line != "":
                            tle_lines.insert(0, name_line)
                            name_line = ""

                        out.append(
                            Element.from_tle(tle_lines, self.name, download_time)
                        )
                    else:  # Assume a name line
                        name_line = line.strip()

                return out
            else:
                logging.error(
                    f"Invalid data type '{self.data_type}' for source {self.name}"
                )
                return None
        except Exception as e:
            logging.error(
                f"Exception while parsing TLE data from source {self.name}: {e}"
            )
            logging.debug(traceback.format_exc())
            return None


def read_sources(file_path: str) -> List[Source]:
    """
    Read TOML config file containing definitions of TLE sources in the following format:

    ```
    [name]
    data_type = ".." # Choices: json, tle
    url = "https://example.com/"
    ...
    ```
    """

    logging.debug(f"Reading sources file at {file_path}")
    with open(file_path, "rb") as f:
        sources = tomllib.load(f)

    out = []
    for name, config in sources.items():
        out.append(Source(name=name, data_type=config["data_type"], url=config["url"]))

    return out
