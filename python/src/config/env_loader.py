"""
Loads environment variables from a .env file.
"""
import os
from pathlib import Path

from dotenv import load_dotenv


class EnvLoader:
    """
    Loads environment variables from a .env file.
    """

    def __init__(self, env_path: str | Path | None = None) -> None:
        """
        Initialize the loader with an optional path to the .env file.
        If not provided, uses .env in the parent of the config package (src directory).
        """
        if env_path is None:
            base = Path(__file__).resolve().parent.parent
            env_path = base / ".env"
        self._env_path = Path(env_path)

    @property
    def env_path(self) -> Path:
        """Path to the .env file."""
        return self._env_path

    def load(self) -> bool:
        """
        Load variables from the .env file.
        Returns True if the file was found and loaded, False otherwise.
        """
        if not self._env_path.exists():
            return False
        load_dotenv(self._env_path)
        return True

    @property
    def ftp_datasus(self) -> str | None:
        """Return the value of FTP_DATASUS loaded from .env."""
        return os.getenv("FTP_DATASUS")

    @property
    def temp_download_path(self) -> str | None:
        """Return the temporary folder path for downloads."""
        return os.getenv("TEMP_DOWNLOAD_PATH")

    @property
    def start_year(self) -> str | None:
        """Return the start year of the period (inclusive)."""
        return os.getenv("START_YEAR")

    @property
    def start_month(self) -> str | None:
        """Return the start month of the period (inclusive)."""
        return os.getenv("START_MONTH")

    @property
    def end_year(self) -> str | None:
        """Return the end year of the period (inclusive)."""
        return os.getenv("END_YEAR")

    @property
    def end_month(self) -> str | None:
        """Return the end month of the period (inclusive)."""
        return os.getenv("END_MONTH")

    @property
    def states(self) -> str | None:
        """Return the comma-separated state codes (UF)."""
        return os.getenv("STATES")

    @property
    def states_list(self) -> list[str]:
        """Return the list of state codes (UF), parsed from the comma-separated STATES value."""
        raw = os.getenv("STATES")
        if not raw or not raw.strip():
            return []
        return [s.strip().upper() for s in raw.split(",") if s.strip()]
