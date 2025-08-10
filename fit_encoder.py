"""FIT file encoder for health data."""

import struct
import time
from datetime import datetime
from io import BytesIO
from typing import Optional


def _calc_crc(crc: int, byte: int) -> int:
    """Calculate CRC for FIT file."""
    table = [
        0x0000,
        0xCC01,
        0xD801,
        0x1400,
        0xF001,
        0x3C00,
        0x2800,
        0xE401,
        0xA001,
        0x6C00,
        0x7800,
        0xB401,
        0x5000,
        0x9C01,
        0x8801,
        0x4400,
    ]

    # Compute checksum of lower four bits of byte
    tmp = table[crc & 0xF]
    crc = (crc >> 4) & 0x0FFF
    crc = crc ^ tmp ^ table[byte & 0xF]

    # Now compute checksum of upper four bits of byte
    tmp = table[crc & 0xF]
    crc = (crc >> 4) & 0x0FFF
    crc = crc ^ tmp ^ table[(byte >> 4) & 0xF]

    return crc


class FitEncoder:
    """Simple FIT file encoder for weight and health data."""

    HEADER_SIZE = 12
    FILE_TYPE_WEIGHT = 9

    # Message numbers
    MSG_FILE_ID = 0
    MSG_DEVICE_INFO = 23
    MSG_WEIGHT_SCALE = 30
    MSG_BLOOD_PRESSURE = 51

    def __init__(self):
        self.buffer = BytesIO()
        self._write_header()
        self._device_info_written = False

    def _write_header(self):
        """Write FIT file header."""
        self.buffer.seek(0)
        header = struct.pack(
            "BBHI4s",
            self.HEADER_SIZE,  # header_size
            16,  # protocol_version
            108,  # profile_version
            0,  # data_size (will be updated)
            b".FIT",
        )  # data_type
        self.buffer.write(header)

    def _timestamp(self, dt: datetime) -> int:
        """Convert datetime to FIT timestamp (seconds since UTC Dec 31, 1989)."""
        if isinstance(dt, datetime):
            timestamp = time.mktime(dt.timetuple())
        else:
            timestamp = dt
        return int(timestamp - 631065600)  # FIT epoch offset

    def _write_definition_message(
        self, local_msg_type: int, global_msg_num: int, fields: list
    ):
        """Write a definition message."""
        # Definition message header
        header = 0x40 | local_msg_type  # 0x40 = definition message flag
        self.buffer.write(struct.pack("B", header))

        # Fixed content
        self.buffer.write(struct.pack("BBHB", 0, 0, global_msg_num, len(fields)))

        # Field definitions
        for field_num, size, base_type in fields:
            self.buffer.write(struct.pack("BBB", field_num, size, base_type))

    def _write_data_message(self, local_msg_type: int, values: list):
        """Write a data message."""
        # Data message header
        self.buffer.write(struct.pack("B", local_msg_type))

        # Write values
        for value, fmt in values:
            if value is None:
                # Write invalid value based on format
                if fmt == "I":
                    value = 0xFFFFFFFF
                elif fmt == "H":
                    value = 0xFFFF
                elif fmt == "B":
                    value = 0xFF
            self.buffer.write(
                struct.pack(fmt, int(value) if value is not None else value)
            )

    def write_file_id(self):
        """Write file ID message."""
        # Definition
        fields = [
            (0, 1, 0x00),  # type (enum)
            (1, 2, 0x84),  # manufacturer (uint16)
            (2, 2, 0x84),  # product (uint16)
            (3, 4, 0x8C),  # serial_number (uint32z)
            (4, 4, 0x86),  # time_created (uint32)
        ]
        self._write_definition_message(0, self.MSG_FILE_ID, fields)

        # Data
        now = datetime.now()
        values = [
            (self.FILE_TYPE_WEIGHT, "B"),  # type
            (1, "H"),  # manufacturer (1 = Garmin)
            (0, "H"),  # product
            (0, "I"),  # serial_number
            (self._timestamp(now), "I"),  # time_created
        ]
        self._write_data_message(0, values)

    def write_device_info(self, timestamp: datetime):
        """Write device info message."""
        if not self._device_info_written:
            # Definition
            fields = [
                (253, 4, 0x86),  # timestamp (uint32)
                (0, 1, 0x02),  # device_index (uint8)
                (1, 1, 0x02),  # device_type (uint8)
                (2, 2, 0x84),  # manufacturer (uint16)
                (4, 2, 0x84),  # product (uint16)
                (5, 2, 0x84),  # software_version (uint16)
            ]
            self._write_definition_message(1, self.MSG_DEVICE_INFO, fields)
            self._device_info_written = True

        # Data
        values = [
            (self._timestamp(timestamp), "I"),  # timestamp
            (0, "B"),  # device_index
            (119, "B"),  # device_type (scale)
            (1, "H"),  # manufacturer (Garmin)
            (0, "H"),  # product
            (100, "H"),  # software_version
        ]
        self._write_data_message(1, values)

    def write_weight_measurement(
        self,
        timestamp: datetime,
        weight: float,
        fat_percentage: Optional[float] = None,
        muscle_mass: Optional[float] = None,
        bone_mass: Optional[float] = None,
        body_water: Optional[float] = None,
    ):
        """Write weight scale measurement."""
        # Definition (only write once)
        if not hasattr(self, "_weight_def_written"):
            fields = [
                (253, 4, 0x86),  # timestamp (uint32)
                (0, 2, 0x84),  # weight (uint16, scale 100)
                (1, 2, 0x84),  # percent_fat (uint16, scale 100)
                (5, 2, 0x84),  # muscle_mass (uint16, scale 100)
                (4, 2, 0x84),  # bone_mass (uint16, scale 100)
                (2, 2, 0x84),  # percent_hydration (uint16, scale 100)
            ]
            self._write_definition_message(2, self.MSG_WEIGHT_SCALE, fields)
            self._weight_def_written = True

        # Data
        values = [
            (self._timestamp(timestamp), "I"),
            (int(weight * 100) if weight else None, "H"),
            (int(fat_percentage * 100) if fat_percentage else None, "H"),
            (int(muscle_mass * 100) if muscle_mass else None, "H"),
            (int(bone_mass * 100) if bone_mass else None, "H"),
            (int(body_water * 100) if body_water else None, "H"),
        ]
        self._write_data_message(2, values)

    def write_blood_pressure(
        self,
        timestamp: datetime,
        systolic: int,
        diastolic: int,
        heart_rate: Optional[int] = None,
    ):
        """Write blood pressure measurement."""
        # Definition (only write once)
        if not hasattr(self, "_bp_def_written"):
            fields = [
                (253, 4, 0x86),  # timestamp (uint32)
                (0, 2, 0x84),  # systolic_pressure (uint16)
                (1, 2, 0x84),  # diastolic_pressure (uint16)
                (6, 1, 0x02),  # heart_rate (uint8)
            ]
            self._write_definition_message(3, self.MSG_BLOOD_PRESSURE, fields)
            self._bp_def_written = True

        # Data
        values = [
            (self._timestamp(timestamp), "I"),
            (systolic, "H"),
            (diastolic, "H"),
            (heart_rate if heart_rate else None, "B"),
        ]
        self._write_data_message(3, values)

    def finalize(self) -> bytes:
        """Finalize the FIT file and return bytes."""
        # Calculate data size
        data_size = self.buffer.tell() - self.HEADER_SIZE

        # Update header with correct data size
        self.buffer.seek(4)
        self.buffer.write(struct.pack("I", data_size))

        # Calculate and append CRC
        self.buffer.seek(0)
        crc = 0
        while True:
            byte_data = self.buffer.read(1)
            if not byte_data:
                break
            crc = _calc_crc(crc, byte_data[0])

        # Append CRC
        self.buffer.write(struct.pack("H", crc))

        # Return the complete file
        self.buffer.seek(0)
        return self.buffer.getvalue()
