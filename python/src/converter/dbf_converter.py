"""
Converts DBF files to other formats (e.g. CSV).
"""

from pathlib import Path

import pandas as pd
from dbfread import DBF


class DBFConverter:
    """
    Converter for DBF files.
    """

    @staticmethod
    def to_csv(dbf_folder: str | Path, dest_folder: str | Path) -> list[Path]:
        """
        Convert all DBF files in the given folder to CSV format.

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
                table = DBF(str(dbf_path))
                df = pd.DataFrame(iter(table))
                df.to_csv(csv_path, index=False, encoding="utf-8")
                result.append(csv_path)
                print(f"File {dbf_path.name} converted to {csv_path.name}")
            except (OSError, Exception):
                pass
        return result
