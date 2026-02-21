"""
Converts DBC files (e.g. DATASUS SIH) to other formats.
"""

from pathlib import Path

from dbctodbf import DBCDecompress


class DBCConverter:
    """
    Converter for DBC (Compressed Database) files.
    Uses pure Python (dbc-to-dbf) to decompress DBC to DBF — no compilation required.
    """

    @staticmethod
    def to_dbf(dbc_folder: str | Path, dest_folder: str | Path) -> list[Path]:
        """
        Convert all DBC files in the given folder to DBF format.

        Args:
            dbc_folder: Folder containing the input DBC files.
            dest_folder: Folder where the output DBF files will be saved.

        Returns:
            List of paths to the created DBF files in the destination folder.
        """
        dbc_folder = Path(dbc_folder)
        dest_folder = Path(dest_folder)
        dest_folder.mkdir(parents=True, exist_ok=True)
        decompress = DBCDecompress()
        result: list[Path] = []
        for dbc_path in sorted(dbc_folder.glob("*.dbc")):
            dbf_path = dest_folder / dbc_path.with_suffix(".dbf").name
            try:
                decompress.decompressFile(str(dbc_path), str(dbf_path))
                result.append(dbf_path)
                print(f"File {dbc_path.name} converted to {dbf_path.name}")
            except (OSError, Exception):
                pass
        return result
