from datetime import datetime
from typing import Any, Dict, Optional, Self


# Should this be SoA instead of AoS?
class Element:
    def __init__(
        self,
        source_name: str,
        download_time: datetime,
        norad_id: int,
        object_id: str,
        epoch: datetime,
        mean_motion: float,
        eccentricity: float,
        inclination: float,
        ra_asc_node: float,
        argument_pericenter: float,
        mean_anomaly: float,
        drag_term: float,
        mean_motion_dot: float,
        mean_motion_ddot: float,
        rev_at_epoch: int,
        ephemeris_type: int,
        classification_type: str,
        element_set_nr: int,
        name: Optional[str],
    ):
        self.source_name = source_name
        self.download_time = download_time
        self.norad_id = norad_id
        self.object_id = object_id
        self.epoch = epoch
        self.mean_motion = mean_motion
        self.eccentricity = eccentricity
        self.inclination = inclination
        self.ra_asc_node = ra_asc_node
        self.argument_pericenter = argument_pericenter
        self.mean_anomaly = mean_anomaly
        self.drag_term = drag_term
        self.mean_motion_dot = mean_motion_dot
        self.mean_motion_ddot = mean_motion_ddot
        self.rev_at_epoch = rev_at_epoch
        self.ephemeris_type = ephemeris_type
        self.classification_type = classification_type
        self.element_set_nr = element_set_nr
        self.name = name

    @classmethod
    def from_omm_json(
        cls, omm: Dict[str, Any], source_name: str, download_time: datetime
    ) -> Self:
        return cls(
            source_name,
            download_time,
            omm["NORAD_CAT_ID"],
            omm["OBJECT_ID"],
            omm["EPOCH"],
            omm["MEAN_MOTION"],
            omm["ECCENTRICITY"],
            omm["INCLINATION"],
            omm["RA_OF_ASC_NODE"],
            omm["ARG_OF_PERICENTER"],
            omm["MEAN_ANOMALY"],
            omm["BSTAR"],
            omm["MEAN_MOTION_DOT"],
            omm["MEAN_MOTION_DDOT"],
            omm["REV_AT_EPOCH"],
            omm["EPHEMERIS_TYPE"],
            omm["CLASSIFICATION_TYPE"],
            omm["ELEMENT_SET_NO"],
            name=omm.get("OBJECT_NAME"),
        )

    def to_omm_json(self) -> Dict[str, Any]:
        out = {
            "NORAD_CAT_ID": self.norad_id,
            "OBJECT_ID": self.object_id,
            "EPOCH": self.epoch,
            "MEAN_MOTION": self.mean_motion,
            "ECCENTRICITY": self.eccentricity,
            "INCLINATION": self.inclination,
            "RA_OF_ASC_NODE": self.ra_asc_node,
            "ARG_OF_PERICENTER": self.argument_pericenter,
            "MEAN_ANOMALY": self.mean_anomaly,
            "BSTAR": self.drag_term,
            "MEAN_MOTION_DOT": self.mean_motion_dot,
            "MEAN_MOTION_DDOT": self.mean_motion_ddot,
            "REV_AT_EPOCH": self.rev_at_epoch,
            "EPHEMERIS_TYPE": self.ephemeris_type,
            "CLASSIFICATION_TYPE": self.classification_type,
            "ELEMENT_SET_NO": self.element_set_nr,
        }

        if self.name is not None:
            out["OBJECT_NAME"] = self.name

        return out
