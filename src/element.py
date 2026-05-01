import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Self, Tuple


def tle_checksum(line: str) -> bool:
    total = 0

    for c in line[:68]:
        if c.isdigit():
            total += int(c)
        elif c == "-":
            total += 1

    return total % 10


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
    def from_json(
        cls, omm: Dict[str, Any], source_name: str, download_time: datetime
    ) -> Self:
        return cls( # TODO: Handle KeyError
            source_name,
            download_time,
            omm["NORAD_CAT_ID"],
            omm["OBJECT_ID"],
            datetime.fromisoformat(omm["EPOCH"]),
            float(omm["MEAN_MOTION"]),
            float(omm["ECCENTRICITY"]),
            float(omm["INCLINATION"]),
            float(omm["RA_OF_ASC_NODE"]),
            float(omm["ARG_OF_PERICENTER"]),
            float(omm["MEAN_ANOMALY"]),
            float(omm["BSTAR"]),
            float(omm["MEAN_MOTION_DOT"]),
            float(omm["MEAN_MOTION_DDOT"]),
            int(omm["REV_AT_EPOCH"]),
            omm["EPHEMERIS_TYPE"],
            omm["CLASSIFICATION_TYPE"],
            int(omm["ELEMENT_SET_NO"]),
            name=omm.get("OBJECT_NAME"),
        )

    def to_json(self) -> Dict[str, Any]:
        out = {
            "NORAD_CAT_ID": self.norad_id,
            "OBJECT_ID": self.object_id,
            "EPOCH": self.epoch.isoformat(),
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

    @classmethod
    def from_tle(
        cls, tle: str | List[str], source_name: str, download_time: datetime
    ) -> Self:
        lines = tle
        if type(lines) is not list:
            lines = tle.strip().splitlines()

        name = None
        if len(lines) == 3:
            name = lines[0].strip()
            lines.pop(0)

        # Verify checksum
        for i, line in enumerate(lines):
            if not (tle_checksum(line) == int(line[68])):
                logging.warning(
                    f"TLE line {i + 1} from source {source_name} failed checksum verification, attempting to parse anyway"
                )

        # Extract data
        intdes_year = int(lines[0][9:11])
        intdes_year = intdes_year + 2000 if intdes_year < 57 else intdes_year + 1900
        intdes = str(intdes_year) + "-" + lines[0][11:17]

        epoch_year = int(lines[0][18:20])
        epoch_year = epoch_year + 2000 if epoch_year < 57 else epoch_year + 1900
        epoch_doy = float(lines[0][20:32])
        epoch_dt = datetime(epoch_year, 1, 1)
        epoch_dt += timedelta(days=epoch_doy - 1)

        drag_term = lines[0][54:61]
        drag_term_seperator = "-" if "-" in drag_term else "+"
        drag_term, zeros = drag_term.split(drag_term_seperator)
        drag_term = float("0." + ("0" * int(zeros)) + drag_term)

        mean_motion_dot = lines[0][33:43].strip()
        if mean_motion_dot.startswith("-"):
            mean_motion_dot = -float("0" + mean_motion_dot[1:])
        else:
            mean_motion_dot = float("0" + mean_motion_dot)

        return cls(
            source_name,
            download_time,
            int(lines[0][2:7]),  # norad id
            intdes,
            epoch_dt,
            float(lines[1][52:63]),  # mean motion
            float("0." + lines[1][26:33]),  # eccentricity
            float(lines[1][8:16]),  # inclination
            float(lines[1][17:25]),  # ra of asc node
            float(lines[1][34:42]),  # arg of pericenter
            float(lines[1][43:51]),  # mean anomaly
            drag_term,
            mean_motion_dot,  # mean motion dot
            0,  # mean motion ddot
            int(lines[1][63:68]),  # rev at epoch
            int(lines[0][62]),  # ephemeris type
            lines[0][7],  # classification type
            int(lines[0][64:68]),  # element set nr
            name=name,
        )

    def to_tle(self) -> Optional[str]:
        if len(str(self.norad_id)) > 5:
            logging.warning(
                f"Can't generate TLE for element with NORAD ID {self.norad_id} since NORAD ID is longer than 5 digits"
            )
            return None

        lines = []

        # Format first data line
        norad_id = str(self.norad_id).zfill(5)[:5]

        epoch_year_start = datetime(self.epoch.year, 1, 1)
        epoch_doy = (self.epoch - epoch_year_start).total_seconds() / 86400.0
        epoch_doy += 1
        epoch_doy = str(round(epoch_doy, 8)).zfill(12)

        drag_term_fmt = f"{self.drag_term:.4e}"
        drag_decimal, drag_exponent = drag_term_fmt.split("e")
        drag_exponent = int(drag_exponent) + 1
        drag_decimal = drag_decimal.replace(".", "")[:5].ljust(5, "0")
        drag_sign = "-" if drag_exponent < 0 else "+"
        drag_term = f"{drag_decimal}{drag_sign}{abs(drag_exponent)}"

        lines.append(
            f"1 {norad_id}{self.classification_type[0]} {str(self.object_id)[2:4]}{self.object_id[5:].rjust(6)} "
            + f"{str(self.epoch.year)[-2:]}{epoch_doy} {'-' if self.mean_motion_dot < 0 else ' '}.{format(abs(self.mean_motion_dot), '.8f')[2:]} "
            + f" 00000+0  {drag_term} {self.ephemeris_type}  {str(self.element_set_nr)[-3:]}"
        )

        # Format second data line
        lines.append(
            f"2 {norad_id} {str(format(self.inclination, '.4f')).rjust(8)} {str(format(self.ra_asc_node, '.4f')).rjust(8)} "
            + f"{format(self.eccentricity, '.7f')[2:]} {str(format(self.argument_pericenter, '.4f')).rjust(8)} "
            + f"{str(format(self.mean_anomaly, '.4f')).rjust(8)} {str(round(self.mean_motion, 8)).ljust(11, '0')}"
            + f"{str(self.rev_at_epoch)[-5:].rjust(5)}"
        )

        # Add checksum
        for i in range(len(lines)):
            lines[i] += str(tle_checksum(lines[i]))

        # Add name line if available
        if self.name is not None:
            lines.insert(0, self.name[:24].ljust(24))

        return "\n".join(lines) + "\n"

    @classmethod
    def from_csv(
        cls, keys_line: str, data_line: str, source_name: str, download_time: datetime
    ) -> Optional[Self]:

        # Parse csv lines to dict
        keys = [k.strip() for k in keys_line.split(",")]
        values = [v.strip() for v in data_line.split(",")]

        if len(keys) != len(values):
            logging.warning(
                f"Failed to parse CSV TLE from source {source_name} since keys line and data line have a mismatching number of elements"
            )
            return None

        data = dict(zip(keys, values))

        return cls.from_json(data, source_name, download_time)

    def to_csv(self) -> str:
        eccentricity = f"{self.eccentricity:g}".upper().replace("0.", ".")
        drag_term = f"{self.drag_term:g}".upper().replace("0.", ".")
        mean_motion_dot = f"{self.mean_motion_dot:g}".upper().replace("0.", ".")

        out = ""
        out += str(self.name) + ","
        out += str(self.object_id) + ","
        out += str(self.epoch.isoformat()) + ","
        out += str(self.mean_motion) + ","
        out += str(eccentricity) + ","
        out += str(self.inclination) + ","
        out += str(self.ra_asc_node) + ","
        out += str(self.argument_pericenter) + ","
        out += str(self.mean_anomaly) + ","
        out += str(self.ephemeris_type) + ","
        out += str(self.classification_type) + ","
        out += str(self.norad_id) + ","
        out += str(self.element_set_nr) + ","
        out += str(self.rev_at_epoch) + ","
        out += str(drag_term) + ","
        out += str(mean_motion_dot) + ","
        out += str(self.mean_motion_ddot)

        return out

