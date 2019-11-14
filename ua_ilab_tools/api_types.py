"""Declares the data types used in transferring requests to projects."""
from dataclasses import dataclass, field


@dataclass
class Researcher:
    """The dataclass the holds the fields for a Researcher."""
    first_name: str
    last_name: str
    lab_type: str
    email: str
    uri: str


@dataclass
class Project:
    """The dataclass the holds the fields for a Project."""
    name: str
    res: str
    open_date: str = ""
    files: list = field(default_factory=list)
    uri: str = ""


@dataclass
class Container:
    """The dataclass the holds the fields for a Container."""
    name: str = ""
    con_type: str = ""
    con_type_uri: str = ""
    uri: str = ""


@dataclass
class Sample:
    """The dataclass the holds the fields for a Sample."""
    name: str
    udf_to_value: dict = field(default_factory=dict)
    adapter: str = ""
    con: None = field(default=None)
    location: str = "1:1"
    uri: str = ""
    art_uri: str = ""


@dataclass
class CustomForm:
    """The dataclass the holds the fields for a CustomForm."""
    name: str
    req_id: str
    form_id: str
    con_type: str = "Tube"
    field_to_values: dict = field(default_factory=dict)
    samples: list = field(default_factory=list)
    request_type: str = ""


@dataclass
class Service_Price:
    """The dataclass that hold the fields for a services price."""
    price: str
    samples_per_unit: str
