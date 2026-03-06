"""
Converts CNV (fixed-width) files to CSV using a CNV schema.
"""

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cnv_schemas.cnv_schema import CNVSchema


class CNVConverter:
    """
    Converter for CNV (fixed-width) files to CSV.
    Uses a CNVSchema to parse each line and write CSV with headers from the schema.
    """

    @staticmethod
    def to_csv(
        cnv_path: str | Path,
        dest_path: str | Path,
        schema: "CNVSchema",
        encoding: str = "utf-8",
    ) -> Path:
        """
        Convert a single CNV (fixed-width) file to CSV according to the given schema.

        Args:
            cnv_path: Path to the input CNV file.
            dest_path: Path to the output CSV file.
            schema: CNVSchema defining field positions, sizes, titles and types.
            encoding: Encoding for reading the CNV file. Defaults to utf-8.

        Returns:
            Path to the created CSV file.

        Raises:
            FileNotFoundError: If the CNV file does not exist.
        """
        cnv_path = Path(cnv_path)
        dest_path = Path(dest_path)
        if not cnv_path.is_file():
            raise FileNotFoundError(f"CNV file not found: {cnv_path}")
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        fields = schema.schema
        with open(cnv_path, "r", encoding=encoding) as f_in:
            with open(dest_path, "w", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(f_out)
                writer.writerow([field.title for field in fields])
                for line in f_in:
                    try:
                        row = CNVConverter._parse_line(line, fields)
                        writer.writerow(row)
                    except Exception:
                        pass  # ignore lines that fail to convert
        print(f"File {cnv_path.name} converted to {dest_path.name}")
        return dest_path

    @staticmethod
    def _parse_line(line: str, fields: list) -> list[str]:
        """
        Parse a single fixed-width line into a list of values (strings for CSV).
        Converts int fields according to the schema; raises ValueError if any int
        cannot be converted, so the caller can ignore that line.
        """
        row: list[str] = []
        for field in fields:
            end = field.pos_start + field.size
            raw = line[field.pos_start:end].rstrip()
            if field.type == "int":
                if not raw.strip():
                    row.append("")
                else:
                    try:
                        row.append(str(int(raw)))
                    except ValueError:
                        raise ValueError(f"Invalid int for field {field.title}: {raw!r}")
            else:
                row.append(raw)
        return row
