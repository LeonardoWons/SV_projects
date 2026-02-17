from typing import TypedDict

class TelemetryDataType(TypedDict):
    """
    Represents the structure of telemetry data collected from the tugger device.

    Attributes:
        EQUIPMENT_ID (str): Unique identifier for the tugger equipment.
        EQUIPMENT_TYPE (str): Type of the equipment (e.g., "Tugger", "Forklift").
        DATE_TIME (str): Timestamp of the telemetry data in "YYYY-MM-DD HH:MM:SS" format.
        LATITUDE (str): GPS latitude coordinate.
        LONGITUDE (str): GPS longitude coordinate.
        ALTITUDE (str): GPS altitude coordinate.
        SIGNAL_QUALITY (str): Signal quality of the GPS.
        SATELLITE_COUNT (str): Number of satellites connected to the GPS.
        PDOP (str): Position Dilution of Precision (PDOP) value.
        HDOP (str): Horizontal Dilution of Precision (HDOP) value.
        VDOP (str): Vertical Dilution of Precision (VDOP) value.
        SPEED (str): Current speed of the tugger.
        DIRECTION (str): Direction of the tugger's movement.
        PHONIC_WHEEL_RPM (str): Current rotation per minute from phonic wheel.
        IS_EQUIPMENT_ON (str): Status indicating if the equipment is turned on.
        ELECTRIC_CURRENT (str): Current electrical current value.
        IS_INTERNET_CONNECTED (str): "1" if the tugger is online, "0" if offline.
        IS_EQUIPMENT_IN_REVERSE (str): Status indicating if the equipment is in reverse gear.
        EMPLOYEE_BADGE (str): Current employee badge ID or "0" if none assigned.
        COMPUTER_HOSTNAME (str): Hostname of the computer running the telemetry system.
        CODE_VERSION (str): Software version of the telemetry system.
    """

    EQUIPMENT_ID: str
    EQUIPMENT_TYPE: str
    DATE_TIME: str

    LATITUDE: str
    LONGITUDE: str
    ALTITUDE: str

    SIGNAL_QUALITY: str
    SATELLITE_COUNT: str

    PDOP: str
    HDOP: str
    VDOP: str

    SPEED: str
    DIRECTION: str

    PHONIC_WHEEL_RPM: str

    IS_EQUIPMENT_ON: str
    ELECTRIC_CURRENT: str

    IS_INTERNET_CONNECTED: str
    IS_EQUIPMENT_IN_REVERSE: str

    EMPLOYEE_BADGE: str
    COMPUTER_HOSTNAME: str
    CODE_VERSION: str