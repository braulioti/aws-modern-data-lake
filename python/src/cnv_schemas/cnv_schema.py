"""
CNV (fixed-width) schema definition: field position, size, title and type.
"""

from dataclasses import dataclass
from typing import Literal

CNVFieldType = Literal["string", "int"]


@dataclass
class CNVField:
    """Single field in a CNV schema: start position, size, title and type."""

    pos_start: int
    size: int
    title: str
    type: CNVFieldType  # noqa: A003


class CNVSchema:
    """
    Schema as an array of field definitions (pos_start, size, title, type).
    Allowed types: 'string' and 'int'.
    """

    def __init__(self, fields: list[CNVField] | None = None) -> None:
        """
        Initialize the schema with a list of field definitions.

        Args:
            fields: List of CNVField (pos_start, size, title, type). Defaults to empty list.
        """
        self._fields: list[CNVField] = list(fields) if fields else []

    @property
    def schema(self) -> list[CNVField]:
        """Schema as an array of field definitions."""
        return self._fields

    def add_field(self, pos_start: int, size: int, title: str, type: CNVFieldType) -> None:  # noqa: A002
        """Append a field to the schema."""
        self._fields.append(CNVField(pos_start=pos_start, size=size, title=title, type=type))
