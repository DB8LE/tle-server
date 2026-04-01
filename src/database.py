import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
from .element import Element

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS elements(
    source_name TEXT,
    download_time TEXT,
    norad_id INT PRIMARY KEY,
    object_id TEXT,
    epoch TEXT,
    mean_motion REAL,
    eccentricity REAL,
    inclination REAL,
    ra_asc_node REAL,
    argument_pericenter REAL,
    mean_anomaly REAL,
    drag_term REAL,
    mean_motion_dot REAL,
    mean_motion_ddot REAL,
    rev_at_epoch INT,
    ephemeris_type INT,
    classification_type TEXT,
    element_set_nr INT,
    name TEXT
)"""

INSERT_ELEMENTS_SQL = """
INSERT OR REPLACE INTO elements (
    source_name, download_time, norad_id, object_id, epoch, mean_motion,
    eccentricity, inclination, ra_asc_node, argument_pericenter, mean_anomaly,
    drag_term, mean_motion_dot, mean_motion_ddot, rev_at_epoch,
    ephemeris_type, classification_type, element_set_nr, name
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)

        cur = self.conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        cur.close()
        self.conn.commit()

    def insert_elements(self, elements: List[Element]):
        logging.debug(f"Inserting {len(elements)} element(s) into database")
        data = [
            (
                e.source_name,
                e.download_time,
                e.norad_id,
                e.object_id,
                e.epoch,
                e.mean_motion,
                e.eccentricity,
                e.inclination,
                e.ra_asc_node,
                e.argument_pericenter,
                e.mean_anomaly,
                e.drag_term,
                e.mean_motion_dot,
                e.mean_motion_ddot,
                e.rev_at_epoch,
                e.ephemeris_type,
                e.classification_type,
                e.element_set_nr,
                e.name,
            )
            for e in elements
        ]

        cur = self.conn.cursor()
        cur.executemany(INSERT_ELEMENTS_SQL, data)
        cur.close()
        self.conn.commit()

    def get_elements(self, norad_ids: List[int]) -> List[Element]:
        logging.debug(f"Getting {len(norad_ids)} element(s) from database")

        placeholders = ",".join(["?"] * len(norad_ids))

        cur = self.conn.cursor()
        cur.execute(
            f"SELECT * FROM elements WHERE norad_id IN ({placeholders})", norad_ids
        )
        results = cur.fetchall()
        cur.close()

        out = []
        for result in results:
            element = Element(*result)
            element.epoch = datetime.fromisoformat(element.epoch)
            element.download_time = datetime.fromisoformat(element.download_time)
            out.append(element)

        return out

    def get_download_times(
        self, norad_ids: List[int]
    ) -> Dict[int, Tuple[datetime, str]]:
        logging.debug(f"Getting {len(norad_ids)} download times from database")

        placeholders = ",".join(["?"] * len(norad_ids))

        cur = self.conn.cursor()
        cur.execute(
            f"SELECT norad_id, download_time, source_name FROM elements WHERE norad_id IN ({placeholders})",
            norad_ids,
        )
        results = cur.fetchall()
        cur.close()

        out = {}
        for result in results:
            out[result[0]] = (datetime.fromisoformat(result[1]), result[2])

        return out
