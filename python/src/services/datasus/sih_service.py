"""
SIH (Sistema de Informações Hospitalares) service for DATASUS FTP.
"""

from dtos import DatasusSIHDTO

from services.datasus_service import DatasusService


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
            download_path="/dissemin/publicos/SIHSUS/200801_/Dados",
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

    def download(self) -> None:
        """Download SIH data from the DATASUS FTP."""
        uris = self._build_datasus_uris()
        for uri in uris:
            print(uri)
