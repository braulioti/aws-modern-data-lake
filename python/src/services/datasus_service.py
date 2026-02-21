"""
DATASUS FTP service.
"""
from abc import ABC, abstractmethod


class DatasusService(ABC):
    """
    Service for interacting with the DATASUS FTP.
    """

    def __init__(
        self,
        ftp_url: str,
        download_path: str | None = None,
        download_folder: str | None = None,
    ) -> None:
        """
        Initialize the service with the FTP URL, download path and download folder.

        Args:
            ftp_url: Full URL or host of the DATASUS FTP (e.g. ftp://ftp.datasus.gov.br).
            download_path: Base path on the FTP server for downloads (e.g. /dissemin/publicos/SIHSUS/200801_/Dados).
            download_folder: Local folder where files will be downloaded.
        """
        self._ftp_url = ftp_url.strip().rstrip("/")
        self._download_path = download_path
        self._download_folder = download_folder

    @property
    def ftp_url(self) -> str:
        """FTP base URL."""
        return self._ftp_url

    @property
    def download_folder(self) -> str | None:
        """Local folder where files will be downloaded."""
        return self._download_folder

    @abstractmethod
    def download(self) -> None:
        """Download data from the DATASUS FTP. Must be implemented by subclasses."""
        ...
