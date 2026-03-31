import logging
import time
from datetime import datetime, timedelta, timezone
from typing import List
from flask import Flask, jsonify, request
from .database import Database
from .element import Element
from .sources import Source


class API:
    def __init__(
        self,
        host: str,
        port: int,
        element_ttl: timedelta,
        database: Database,
        sources: List[Source],
    ):
        self.host = host
        self.port = port
        self.element_ttl = element_ttl
        self.database = database

        self.sources = {}
        for source in sources:
            self.sources[source.name] = source

        self.app = Flask("tle-server")

        # Register routes
        self.app.add_url_rule("/elements", "elements", self.elements, methods=["GET"])

    def _get_elements(self, norad_ids: List[int], timeout: int = 10) -> List[Element]:
        # TODO: Maybe optimise this algorithm to get the most efficient sources list to download all elements that are too old
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            for id in norad_ids:
                elements = self.database.get_elements([id])
                if len(elements) == 0:  # More than 1 result isn't possible
                    logging.debug(
                        f"Element for NORAD ID {id} isn't available in database, skipping"
                    )
                    continue
                element = elements[0]

                age = datetime.now(timezone.utc) - element.download_time
                if age > self.element_ttl:
                    # Find elements source
                    if element.source_name not in self.sources.keys():
                        logging.error(
                            f"Element for NORAD ID {element.norad_id} contains source name not in sources list"
                        )
                        return []
                    source = self.sources[element.source_name]

                    # Re-download the source
                    logging.info(
                        f"Redownloading source {element.source_name} because element for NORAD ID {element.norad_id} is beyond ttl"
                    )
                    elements = source.fetch()
                    self.database.insert_elements(elements)

                    # Restart check
                    break

            # All elements are up-to-date
            return self.database.get_elements(norad_ids)

    def elements(self):
        norad_ids = request.args.getlist("norad")
        format = request.args.get("format")

        # Check if parameters were provided
        if not format:
            return "ERROR: Missing required parameter format", 400

        if len(norad_ids) == 0:
            return "ERROR: Must specify at least one norad id", 400

        # Make DB request
        elements = self._get_elements(norad_ids)

        if len(elements) == 0:
            return "ERROR: Not in database", 404

        if format == "omm_json":
            out = []
            for element in elements:
                out.append(element.to_omm_json())

            return jsonify(out)
        else:
            return "ERROR: Invalid format", 400

        return f"{norad_ids} {format}"

    def run(self):
        self.app.run(host=self.host, port=self.port)
