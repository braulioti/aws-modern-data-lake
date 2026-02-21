"""
Loads environment variables. Prefers existing env (e.g. Docker); falls back to .env file; then defaults.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Defaults when neither env nor .env is set (match .env.example)
_DEFAULTS = {
    "FTP_DATASUS": "ftp://ftp.datasus.gov.br",
    "TEMP_DOWNLOAD_PATH": "../tmp",
    "TEMP_DBC_PATH": "../tmp/dbc",
    "TEMP_DBF_PATH": "../tmp/dbf",
    "TEMP_CSV_PATH": "../tmp/csv",
    "START_YEAR": "2023",
    "START_MONTH": "1",
    "END_YEAR": "2023",
    "END_MONTH": "10",
    "STATES": "SP,RJ,MG",
}


class EnvLoader:
    """
    Loads configuration from environment variables.
    By default, values already set in the environment (e.g. by Docker) are used;
    if not set, variables are loaded from the .env file.
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
        Load variables from the .env file into the environment.
        Does not override variables already set (e.g. by Docker). Returns True
        if the .env file was found and loaded, False otherwise.
        """
        if not self._env_path.exists():
            return False
        load_dotenv(self._env_path, override=False)
        return True

    def _get(self, key: str) -> str:
        """Return env value or default."""
        return os.getenv(key) or _DEFAULTS.get(key, "")

    @property
    def ftp_datasus(self) -> str:
        """Return the value of FTP_DATASUS (env, .env, or default)."""
        return self._get("FTP_DATASUS")

    @property
    def temp_download_path(self) -> str:
        """Return the temporary folder path for downloads."""
        return self._get("TEMP_DOWNLOAD_PATH")

    @property
    def temp_dbc_path(self) -> str:
        """Return the temporary folder path for DBC files."""
        return self._get("TEMP_DBC_PATH")

    @property
    def temp_dbf_path(self) -> str:
        """Return the temporary folder path for converted DBF files."""
        return self._get("TEMP_DBF_PATH")

    @property
    def temp_csv_path(self) -> str:
        """Return the temporary folder path for converted CSV files."""
        return self._get("TEMP_CSV_PATH")

    @property
    def start_year(self) -> str:
        """Return the start year of the period (inclusive)."""
        return self._get("START_YEAR")

    @property
    def start_month(self) -> str:
        """Return the start month of the period (inclusive)."""
        return self._get("START_MONTH")

    @property
    def end_year(self) -> str:
        """Return the end year of the period (inclusive)."""
        return self._get("END_YEAR")

    @property
    def end_month(self) -> str:
        """Return the end month of the period (inclusive)."""
        return self._get("END_MONTH")

    @property
    def states(self) -> str:
        """Return the comma-separated state codes (UF)."""
        return self._get("STATES")

    @property
    def states_list(self) -> list[str]:
        """Return the list of state codes (UF), parsed from the comma-separated STATES value."""
        raw = self._get("STATES")
        if not raw or not raw.strip():
            return []
        return [s.strip().upper() for s in raw.split(",") if s.strip()]
