"""
DATASUS integration for FTP access and SIH (and future) services used by the pipeline.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cnv_schemas.cnv_schema import CNVSchema
    from dtos import DatasusSIHDTO

from pathlib import Path

from cnv_schemas import CNVCitySchema
from converter import CNVConverter, DBCConverter, DBFConverter, ZipConverter
from services.datasus import DatasusIBGEService, DatasusSIHService

# CNV municip file path relative to extract folder; output filename
CNV_MUNICIP_REL_PATH = "CNV/br_municip.cnv"
MUNICIPIOS_CSV_FILENAME = "MUNICIPIOS.CSV"


class DatasusIntegration:
    """
    Centralizes DATASUS FTP URL and creation of DATASUS services (e.g. SIH download).
    """

    def __init__(self, ftp_url: str = "") -> None:
        """
        Initialize DATASUS integration.

        Args:
            ftp_url: Base URL of the DATASUS FTP (e.g. ftp://ftp.datasus.gov.br).
        """
        self._ftp_url = (ftp_url or "").strip().rstrip("/")

    @property
    def ftp_url(self) -> str:
        """DATASUS FTP base URL."""
        return self._ftp_url

    def create_sih_service(
        self,
        params: "DatasusSIHDTO",
        download_folder: str | None = None,
        ignore_files_sih: list[str] | None = None,
    ) -> DatasusSIHService:
        """
        Create the SIH (Sistema de Informações Hospitalares) download service.

        Args:
            params: SIH parameters (period and state filters).
            download_folder: Local folder where DBC files will be downloaded.
            ignore_files_sih: List of file names to skip for SIH (e.g. already in S3).

        Returns:
            Configured DatasusSIHService instance (call .download() to run).
        """
        return DatasusSIHService(
            ftp_url=self._ftp_url,
            params=params,
            download_folder=download_folder,
            ignore_files=ignore_files_sih or [],
        )

    def run_converters(
        self,
        temp_dbc_path: str | None,
        temp_dbf_path: str | None,
        temp_csv_path: str | None,
    ) -> None:
        """
        Run DBC -> DBF -> CSV conversion pipeline (SIH).

        Args:
            temp_dbc_path: Folder with DBC files (input).
            temp_dbf_path: Folder for DBF output (and input to CSV step).
            temp_csv_path: Folder for CSV output.
        """
        if temp_dbc_path and temp_dbf_path:
            DBCConverter.to_dbf(temp_dbc_path, temp_dbf_path)
        if temp_dbf_path and temp_csv_path:
            DBFConverter.to_csv(temp_dbf_path, temp_csv_path)

    def process_ibge(
        self,
        temp_zip_folder: str | None = None,
        temp_zip_extract_folder: str | None = None,
        csv_ibge_folder: str | None = None,
    ) -> None:
        """
        Run IBGE pipeline: download TAB_POP.zip, extract ZIPs, convert br_municip.cnv to MUNICIPIOS.CSV.

        Args:
            temp_zip_folder: Folder where IBGE ZIP (TAB_POP.zip) is downloaded.
            temp_zip_extract_folder: Destination folder for extracted ZIP contents.
            csv_ibge_folder: Folder where MUNICIPIOS.CSV will be written.
        """
        if temp_zip_folder:
            ibge_service = DatasusIBGEService(
                ftp_url=self._ftp_url,
                download_folder=temp_zip_folder,
            )
            ibge_service.download()
        if temp_zip_folder and temp_zip_extract_folder:
            zip_dir = Path(temp_zip_folder)
            for zip_path in zip_dir.glob("*.zip"):
                try:
                    ZipConverter.extract(zip_path, temp_zip_extract_folder)
                except (FileNotFoundError, Exception):
                    pass
        if temp_zip_extract_folder and csv_ibge_folder:
            cnv_municip_path = Path(temp_zip_extract_folder) / CNV_MUNICIP_REL_PATH
            municipios_csv_path = Path(csv_ibge_folder) / MUNICIPIOS_CSV_FILENAME
            if cnv_municip_path.is_file():
                try:
                    Path(csv_ibge_folder).mkdir(parents=True, exist_ok=True)
                    CNVConverter.to_csv(
                        cnv_municip_path,
                        municipios_csv_path,
                        CNVCitySchema(),
                        encoding="latin-1",
                    )
                except (FileNotFoundError, Exception) as e:
                    print(f"Error converting {cnv_municip_path.name} to {MUNICIPIOS_CSV_FILENAME}: {e}")

    def convert_cnv_files(
        self,
        cnv_folder: str | None,
        dest_folder: str | None,
        schema: "CNVSchema",
        encoding: str = "utf-8",
    ) -> list[Path]:
        """
        Convert each CNV file in cnv_folder to CSV in dest_folder using the given schema.
        Calls CNVConverter.to_csv for each .cnv file (one file per conversion).

        Args:
            cnv_folder: Folder containing .cnv files (e.g. extracted ZIP contents).
            dest_folder: Folder where CSV files will be written.
            schema: CNVSchema defining field positions, sizes, titles and types.
            encoding: Encoding for reading CNV files. Defaults to utf-8.

        Returns:
            List of paths to the created CSV files.
        """
        if not cnv_folder or not dest_folder:
            return []
        cnv_dir = Path(cnv_folder)
        dest_dir = Path(dest_folder)
        dest_dir.mkdir(parents=True, exist_ok=True)
        result: list[Path] = []
        for cnv_path in sorted(cnv_dir.glob("*.cnv")):
            csv_path = dest_dir / cnv_path.with_suffix(".csv").name
            try:
                result.append(CNVConverter.to_csv(cnv_path, csv_path, schema, encoding=encoding))
            except (FileNotFoundError, Exception) as e:
                print(f"Error converting {cnv_path.name}: {e}")
        return result

    def process_datasus(
        self,
        params: "DatasusSIHDTO",
        download_folder: str | None = None,
        ignore_files_sih: list[str] | None = None,
        temp_dbf_path: str | None = None,
        temp_csv_path: str | None = None,
        temp_zip_folder: str | None = None,
        temp_zip_extract_folder: str | None = None,
        csv_ibge_folder: str | None = None,
    ) -> None:
        """
        Run SIH download and converters (DBC -> DBF -> CSV), then process_ibge (download, extract, CNV -> MUNICIPIOS.CSV).

        Args:
            params: SIH parameters (period and state filters).
            download_folder: Local folder where DBC files will be downloaded.
            ignore_files_sih: List of file names to skip for SIH (e.g. already in S3).
            temp_dbf_path: Folder for DBF output (optional; if set with temp_csv_path, SIH converters run).
            temp_csv_path: Folder for CSV output (optional; if set with temp_dbf_path, SIH converters run).
            temp_zip_folder: Folder for IBGE ZIP files (optional; passed to process_ibge).
            temp_zip_extract_folder: Destination for extracted ZIP contents (optional; passed to process_ibge).
            csv_ibge_folder: Folder for IBGE CSV output e.g. MUNICIPIOS.CSV (optional; passed to process_ibge).
        """
        service = self.create_sih_service(params, download_folder, ignore_files_sih or [])
        service.download()
        if download_folder and temp_dbf_path and temp_csv_path:
            self.run_converters(download_folder, temp_dbf_path, temp_csv_path)
        self.process_ibge(
            temp_zip_folder=temp_zip_folder,
            temp_zip_extract_folder=temp_zip_extract_folder,
            csv_ibge_folder=csv_ibge_folder,
        )
