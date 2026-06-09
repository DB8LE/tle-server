import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List
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
        groups: Dict[str, List[int]],
        sources: List[Source],
    ):
        self.host = host
        self.port = port
        self.element_ttl = element_ttl
        self.database = database
        self.base_groups = groups

        self.sources = {}
        for source in sources:
            self.sources[source.name] = source

        self.app = Flask("tle-server")

        self.inherited_groups = {}
        self.groups = {}
        self._update_groups()

        # Register routes
        self.app.add_url_rule("/elements", "elements", self.elements, methods=["GET"])
        self.app.add_url_rule("/stats", "stats", self.stats, methods=["GET"])

    def _update_groups(self):
        self.inherited_groups = self.database.get_inherited_groups()

        # Merge base and inherited groups
        merged_dict = defaultdict(list)

        for d in (self.base_groups, self.inherited_groups):
            for name, ids in d.items():
                merged_dict[name].extend(ids)

        self.groups = dict(merged_dict)

        logging.debug(f"Updated groups. Available groups: {list(self.groups.keys())}")

    def _get_elements(self, norad_ids: List[int], timeout: int = 10) -> List[Element]:
        # TODO: Maybe optimise this algorithm to get the most efficient sources list to download all elements that are too old
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            download_times = self.database.get_download_times(norad_ids)
            for id in norad_ids:
                if len(download_times) == 0:  # More than 1 result isn't possible
                    logging.debug(
                        f"Element for NORAD ID {id} isn't available in database, skipping"
                    )
                    continue

                download_time, source_name = download_times[int(id)]
                age = datetime.now(timezone.utc) - download_time
                if age > self.element_ttl:
                    # Find elements source
                    if source_name not in self.sources.keys():
                        logging.error(
                            f"Element for NORAD ID {id} contains source name not in sources list"
                        )
                        return []
                    source = self.sources[source_name]

                    # Re-download the source
                    logging.info(
                        f"Redownloading source {source_name} because element for NORAD ID {id} is beyond ttl"
                    )
                    self.database.update_from_source(source)

                    # Restart check
                    break

            # All elements are up-to-date
            self._update_groups()
            return self.database.get_elements(norad_ids)

        logging.warning("Couldn't download all required sources in time")
        return []

    def elements(self):
        filter_groups = request.args.getlist("group")
        norad_ids = request.args.getlist("norad")
        format = request.args.get("format")

        # Check if parameters were provided
        if not format:
            return "ERROR: Missing required parameter format", 400

        if (len(norad_ids) == 0) and (len(filter_groups) == 0):
            return "ERROR: Must specify at least one group or norad id", 400

        # Resolve groups to NORAD IDs
        for group in filter_groups:
            if group not in self.groups.keys():
                return f"ERROR: Invalid group '{group}'", 404

            ids = self.groups[group]
            norad_ids.extend(ids)

        # Make DB request
        elements = self._get_elements(norad_ids)

        if len(elements) == 0:
            return "ERROR: Elements not in database", 404

        if format == "json":
            out = []
            for element in elements:
                out.append(element.to_json())

            return jsonify(out)
        elif format == "tle":
            out = ""
            for element in elements:
                tle = element.to_tle()
                out += "" if tle is None else tle
            return f"<pre>{out.strip()}</pre>"
        elif format == "csv":
            out = "OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT\n"
            for element in elements:
                out = out + element.to_csv() + "\n"

            return f"<pre>{out.strip()}</pre>"
        else:
            return "ERROR: Invalid format", 400

        return f"{norad_ids} {format}"

    def stats(self):
        sources = {}
        for name, source in self.sources.items():
            sources[name] = {"url": source.url, "last_fetched": source.last_fetched.timestamp()}

        stats = {}

        stats["element_count"] = self.database.get_element_count()
        stats["groups"] = self.groups
        stats["sources"] = sources

        return jsonify(stats)

    def run(self):
        self.app.run(host=self.host, port=self.port)
