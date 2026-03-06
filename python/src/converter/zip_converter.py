"""
Extracts ZIP archives.
"""

import zipfile
from pathlib import Path


class ZipConverter:
    """
    Converter for ZIP files (extract contents to a folder).
    """

    @staticmethod
    def extract(zip_path: str | Path, dest_folder: str | Path) -> Path:
        """
        Extract a ZIP file to the given destination folder.

        Args:
            zip_path: Path to the ZIP file.
            dest_folder: Folder where the contents will be extracted.

        Returns:
            Path to the destination folder.

        Raises:
            FileNotFoundError: If the ZIP file does not exist.
            zipfile.BadZipFile: If the file is not a valid ZIP archive.
        """
        zip_path = Path(zip_path)
        dest_folder = Path(dest_folder)
        if not zip_path.is_file():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        dest_folder.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest_folder)
        print(f"Extracted {zip_path.name} to {dest_folder}")
        return dest_folder
