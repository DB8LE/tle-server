import argparse
import logging
import os
import time
from datetime import timedelta

from . import custom_logging
from .api import API
from .groups import read_groups
from .sources import read_sources
from .database import Database


def main():
    # Set up logging
    custom_logging.set_up_logging()

    # Parse commandline arguments
    parser = argparse.ArgumentParser(prog="tle-server")
    parser.add_argument(
        "--debug", action="store_true", help="Set logging level to debug"
    )
    parser.add_argument(
        "-c",
        "--conf-path",
        dest="conf_path",
        help="Directory containing sources configuration and database (default: ./)",
    )
    parser.add_argument(
        "-a",
        "--host",
        help="Host address of API (default: localhost)",
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Port of API (default: 5000)",
    )
    parser.add_argument(
        "-t",
        "--element-ttl",
        dest="element_ttl",
        help="Cached element time-to-live in hours (default: 2h)",
    )
    args = parser.parse_args()

    config_path = args.conf_path if args.conf_path else "./"
    element_ttl = (
        timedelta(hours=int(args.element_ttl))
        if args.element_ttl
        else timedelta(hours=2)
    )

    if args.debug:
        custom_logging.set_debug()

    database_path = os.path.join(config_path, "database.db")
    groups_path = os.path.join(config_path, "groups.toml")
    sources_path = os.path.join(config_path, "sources.toml")

    database_empty = not os.path.exists(database_path)
    db = Database(database_path)

    groups = read_groups(groups_path)
    sources = read_sources(sources_path)

    # If database was newly created, download all elements on first run
    if database_empty:
        start_time = time.time()
        element_count = 0
        for source in sources:
            elements = source.fetch()
            db.insert_elements(elements)
            element_count += len(elements)
        run_time = time.time() - start_time
        logging.info(
            f"Downloaded {element_count} elements from all sources in {round(run_time * 1000, 1)}ms"
        )

    api_host = args.host if args.host else "localhost"
    api_port = args.port if args.port else 5000

    api = API(
        host=api_host,
        port=api_port,
        element_ttl=element_ttl,
        database=db,
        groups=groups,
        sources=sources,
    )

    api.run()
