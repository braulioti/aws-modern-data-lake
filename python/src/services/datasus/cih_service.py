"""
CIH (Centro de Informação em Saúde) service for DATASUS pipeline.
Downloads TAB_CIH.zip from the CIH Auxiliar path on the DATASUS FTP.
"""

import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from dtos import FileDownloadStatusDTO

from services.datasus_service import DatasusService

FTP_TIMEOUT = 60

# Default: TAB_CIH.zip from DATASUS CIH Auxiliar (200801_201012)
DEFAULT_CIH_DOWNLOAD_PATH = "/dissemin/publicos/CIH/200801_201012/Auxiliar"
DEFAULT_CIH_FILE_LIST = ["TAB_CIH.zip"]


class DatasusCIHService(DatasusService):
    """
    Service for CIH (Centro de Informação em Saúde) auxiliary data on the DATASUS FTP.
    By default downloads TAB_CIH.zip from /dissemin/publicos/CIH/200801_201012/Auxiliar
    into the given folder. Skips download if the file already exists.
    """

    def __init__(
        self,
        ftp_url: str,
        download_path: str | None = None,
        download_folder: str | None = None,
        ignore_files: list[str] | None = None,
        file_list: list[str] | None = None,
    ) -> None:
        """
        Initialize the CIH service.

        Args:
            ftp_url: Base URL of the FTP (e.g. ftp://ftp.datasus.gov.br).
            download_path: Path on the FTP server; defaults to /dissemin/publicos/CIH/200801_201012/Auxiliar.
            download_folder: Local folder where files will be downloaded.
            ignore_files: List of file names to skip.
            file_list: File names to download; defaults to [TAB_CIH.zip]. If file already
                exists in download_folder, it is not downloaded again.
        """
        path = download_path if download_path and download_path.strip() else DEFAULT_CIH_DOWNLOAD_PATH
        files = list(file_list) if file_list else list(DEFAULT_CIH_FILE_LIST)
        super().__init__(
            ftp_url,
            download_path=path,
            download_folder=download_folder,
            ignore_files=ignore_files,
        )
        self._file_list = files

    @property
    def file_list(self) -> list[str]:
        """List of file names to download from the FTP path."""
        return self._file_list

    def _build_datasus_uris(self) -> list[str]:
        """Build full URIs for each file in file_list under the configured path."""
        path = (self._download_path or "").strip().rstrip("/")
        base = f"{self.ftp_url}{path}/" if path else f"{self.ftp_url}/"
        return [f"{base}{name}" for name in self._file_list]

    def download(self) -> None:
        """Download CIH (or configured) files from the FTP. Skips files in ignore_files or already on disk."""
        if not self.download_folder:
            return
        self._download_status_list.clear()
        folder = Path(self.download_folder)
        folder.mkdir(parents=True, exist_ok=True)
        uris = self._build_datasus_uris()
        for uri in uris:
            filename = Path(urlparse(uri).path).name
            if filename in self.ignore_files:
                self._download_status_list.append(FileDownloadStatusDTO(filename, "ignored"))
                print(f"File {filename} ignored (in ignore_files).")
                continue
            local_path = folder / filename
            if local_path.exists():
                self._download_status_list.append(FileDownloadStatusDTO(filename, "exists"))
                print(f"File {filename} already exists.")
                continue
            try:
                with urllib.request.urlopen(uri, timeout=FTP_TIMEOUT) as response:
                    with open(local_path, "wb") as out_file:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            out_file.write(chunk)
                self._download_status_list.append(FileDownloadStatusDTO(filename, "success"))
                print(f"Downloading {filename}... [OK]")
            except OSError as e:
                self._download_status_list.append(FileDownloadStatusDTO(filename, "error"))
                print(f"Downloading {filename}... [ERROR] ({e})")
