"""
SIH (Sistema de Informações Hospitalares) service for DATASUS FTP.
"""

from ftplib import FTP, error_perm as ftp_error_perm
from pathlib import Path
from urllib.parse import urlparse

from dtos import DatasusSIHDTO, FileDownloadStatusDTO

from services.datasus_service import DatasusService

FTP_TIMEOUT = 60


class DatasusSIHService(DatasusService):
    """
    Service for SIH (Sistema de Informações Hospitalares) data on the DATASUS FTP.
    Extends DatasusService with the same FTP URL.
    """

    def __init__(
        self,
        ftp_url: str,
        params: DatasusSIHDTO,
        download_folder: str | None = None,
    ) -> None:
        """
        Initialize the SIH service with the FTP URL, SIH parameters and download folder.

        Args:
            ftp_url: Full URL or host of the DATASUS FTP (e.g. ftp://ftp.datasus.gov.br).
            params: DTO with period and state filters (start/end year-month, states).
            download_folder: Local folder where files will be downloaded.
        """
        super().__init__(
            ftp_url,
            download_path="/dissemin/publicos/SIHSUS",  # base; per-month path is {aamm}_/Dados
            download_folder=download_folder,
        )
        self._params = params

    @property
    def params(self) -> DatasusSIHDTO:
        """SIH parameters (period and states)."""
        return self._params

    def _build_datasus_uris(self) -> list[str]:
        """
        Build a list of URIs for SIH DBC files following the rule: RD + UF + AAMM + .dbc.
        Iterates from the start date to the end date (params) and generates one URI per month
        per state.
        """
        try:
            start_year = int(self._params.start_year)
            start_month = int(self._params.start_month)
            end_year = int(self._params.end_year)
            end_month = int(self._params.end_month)
        except (TypeError, ValueError):
            return []

        states = self._params.states
        if not states:
            return []

        uris: list[str] = []
        path = self._download_path.rstrip("/") if self._download_path else ""
        base = f"{self.ftp_url}{path}/" if path else f"{self.ftp_url}/"

        y, m = start_year, start_month
        while (y, m) <= (end_year, end_month):
            aamm = f"{y % 100:02d}{m:02d}"
            for uf in states:
                filename = f"RD{uf}{aamm}.dbc"
                uris.append(f"{base}{filename}")
            m += 1
            if m > 12:
                m = 1
                y += 1

        return uris

    def _ftp_host(self) -> str:
        """Extract FTP host from ftp_url (e.g. ftp://ftp.datasus.gov.br -> ftp.datasus.gov.br)."""
        parsed = urlparse(self.ftp_url if "://" in self.ftp_url else "ftp://" + self.ftp_url)
        return parsed.hostname or parsed.path or "ftp.datasus.gov.br"

    def _remote_dir_for(self, filename: str) -> str:
        """
        DATASUS SIH path per month: SIHSUS/{AAMM}_/Dados.
        Filename format: RD{UF}{AAMM}.dbc -> AAMM at index 4:8 (e.g. RDSP2601 -> 2601).
        """
        if len(filename) >= 8 and filename.lower().endswith(".dbc"):
            aamm = filename[4:8]
            base = (self._download_path or "").strip().rstrip("/")
            return f"{base}/{aamm}_/Dados" if base else f"{aamm}_/Dados"
        base = (self._download_path or "").strip().rstrip("/")
        return f"{base}/Dados" if base else "Dados"

    def download(self) -> None:
        """Download SIH data from the DATASUS FTP via ftplib. Skips files that already exist."""
        if not self.download_folder:
            return
        self._download_status_list.clear()
        folder = Path(self.download_folder)
        folder.mkdir(parents=True, exist_ok=True)
        uris = self._build_datasus_uris()
        if not uris:
            return
        host = self._ftp_host()
        try:
            with FTP(host, timeout=FTP_TIMEOUT) as ftp:
                ftp.login()
                for uri in uris:
                    filename = Path(urlparse(uri).path).name
                    local_path = folder / filename
                    if local_path.exists():
                        self._download_status_list.append(
                            FileDownloadStatusDTO(filename, "exists")
                        )
                        print(f"File {filename} already exists.")
                        continue
                    try:
                        remote_dir = self._remote_dir_for(filename)
                        ftp.cwd(remote_dir)
                        with open(local_path, "wb") as f:
                            ftp.retrbinary(f"RETR {filename}", f.write)
                        self._download_status_list.append(
                            FileDownloadStatusDTO(filename, "success")
                        )
                        print(f"Downloading {filename}... [OK]")
                    except (OSError, ftp_error_perm) as e:
                        self._download_status_list.append(
                            FileDownloadStatusDTO(filename, "error")
                        )
                        print(f"Downloading {filename}... [ERROR] ({e})")
        except OSError as e:
            print(f"FTP connection failed: {e}")
