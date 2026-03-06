"""
Converts DBF files to other formats (e.g. CSV).
"""

import csv
from pathlib import Path

from dbfread import DBF


class DBFConverter:
    """
    Converter for DBF files.
    """

    @staticmethod
    def to_csv(dbf_path: str | Path, csv_path: str | Path) -> Path:
        """
        Convert a single DBF file to CSV format.
        Uses streaming (load=False) to avoid loading entire DBF into memory.

        Args:
            dbf_path: Path to the input DBF file.
            csv_path: Path where the output CSV file will be saved.

        Returns:
            Path to the created CSV file.
        """
        dbf_path = Path(dbf_path)
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        table = DBF(str(dbf_path), load=False)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(table.field_names)
            for record in table:
                writer.writerow(list(record.values()))
        return csv_path

    @staticmethod
    def to_csv_folder(dbf_folder: str | Path, dest_folder: str | Path) -> list[Path]:
        """
        Convert all DBF files in the given folder to CSV format.
        Uses streaming (load=False) to avoid loading entire DBF into memory.

        Args:
            dbf_folder: Folder containing the input DBF files.
            dest_folder: Folder where the output CSV files will be saved.

        Returns:
            List of paths to the created CSV files in the destination folder.
        """
        dbf_folder = Path(dbf_folder)
        dest_folder = Path(dest_folder)
        dest_folder.mkdir(parents=True, exist_ok=True)

        result: list[Path] = []

        for dbf_path in sorted(dbf_folder.glob("*.dbf")):
            csv_path = dest_folder / dbf_path.with_suffix(".csv").name
            try:
                DBFConverter.to_csv(dbf_path, csv_path)
                result.append(csv_path)
                print(f"File {dbf_path.name} converted to {csv_path.name}")
            except Exception as e:
                print(f"Error converting {dbf_path.name}: {e}")

        return result
