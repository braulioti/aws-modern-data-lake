"""
DATASUS integration for FTP access and SIH (and future) services used by the pipeline.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cnv_schemas.cnv_schema import CNVSchema
    from config import EnvLoader
    from dtos import DatasusSIHDTO

from cnv_schemas import CNVMunicipioSchema, CNVUFSchema
from converter import CNVConverter, DBCConverter, DBFConverter, ZipConverter
from services.datasus import DatasusCIHService, DatasusIBGEService, DatasusSIHService

from integration.aws_integration import AWSIntegration

# S3 prefix for SIH CSV (used to build ignore_files_sih from existing objects)
S3_RAW_SIH_PREFIX = "raw/sih/"
# CIH ZIP filename (downloaded to zip folder, extracted to extract folder)
CIH_ZIP_FILENAME = "TAB_CIH.zip"
# SIGTAP DBF file (inside extract folder) and output CSV name
SIGTAP_DBF_FILENAME = "TB_SIGTAP.DBF"
SIGTAP_CSV_FILENAME = "TB_SIGTAP.CSV"
# CID10 DBF file (inside extract folder) and output CSV name
CID10_DBF_FILENAME = "CID10.DBF"
CID10_CSV_FILENAME = "CID10.CSV"
# CNV municip file path relative to extract folder; output filename
CNV_MUNICIP_REL_PATH = "CNV/br_municip.cnv"
MUNICIPIOS_CSV_FILENAME = "MUNICIPIOS.CSV"
CNV_UF_REL_PATH = "CNV/br_uf.cnv"
UF_CSV_FILENAME = "UF.CSV"


class DatasusIntegration:
    """
    Centralizes DATASUS FTP URL and creation of DATASUS services (e.g. SIH download).
    When built with EnvLoader, process_datasus() reads all paths and options from it.
    """

    def __init__(self, loader: "EnvLoader") -> None:
        """
        Initialize DATASUS integration with EnvLoader (paths and options read from it in process_datasus).

        Args:
            loader: EnvLoader instance (after load()); used by process_datasus() for all paths and flags.
        """
        self._loader = loader
        self._ftp_url = (loader.ftp_datasus or "").strip().rstrip("/")

    @property
    def ftp_url(self) -> str:
        """DATASUS FTP base URL."""
        return self._ftp_url

    def _ignore_files_sih_from_s3(self) -> list[str]:
        """List CSV keys in S3 (raw/sih/), return corresponding .dbc names to skip on download."""
        bucket = self._loader.aws_s3_bucket
        if not bucket:
            return []
        aws = AWSIntegration()
        keys = aws.list_s3_bucket(bucket, prefix=S3_RAW_SIH_PREFIX)
        return [
            Path(k).with_suffix(".dbc").name
            for k in keys
            if Path(k).name.endswith(".csv")
        ]

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
        temp_zip_extract_folder: str | None = None,
        csv_ibge_sigtap_folder: str | None = None,
        csv_ibge_cid10_folder: str | None = None,
    ) -> None:
        """
        Run DBC -> DBF -> CSV conversion pipeline (SIH), and optionally convert TB_SIGTAP.DBF and CID10.DBF from extract to their CSV folders.

        Args:
            temp_dbc_path: Folder with DBC files (input).
            temp_dbf_path: Folder for DBF output (and input to CSV step).
            temp_csv_path: Folder for CSV output.
            temp_zip_extract_folder: Folder where ZIPs were extracted (e.g. contains TB_SIGTAP.DBF, CID10.DBF).
            csv_ibge_sigtap_folder: Folder where TB_SIGTAP.CSV will be written.
            csv_ibge_cid10_folder: Folder where CID10.CSV will be written.
        """
        if temp_dbc_path and temp_dbf_path:
            DBCConverter.to_dbf_folder(temp_dbc_path, temp_dbf_path)
        if temp_dbf_path and temp_csv_path:
            DBFConverter.to_csv_folder(temp_dbf_path, temp_csv_path)
        if temp_zip_extract_folder and csv_ibge_sigtap_folder:
            sigtap_dbf = Path(temp_zip_extract_folder) / SIGTAP_DBF_FILENAME
            sigtap_csv = Path(csv_ibge_sigtap_folder) / SIGTAP_CSV_FILENAME
            if sigtap_dbf.is_file():
                try:
                    Path(csv_ibge_sigtap_folder).mkdir(parents=True, exist_ok=True)
                    DBFConverter.to_csv(sigtap_dbf, sigtap_csv)
                except (FileNotFoundError, Exception) as e:
                    print(f"Error converting {SIGTAP_DBF_FILENAME} to {SIGTAP_CSV_FILENAME}: {e}")
        if temp_zip_extract_folder and csv_ibge_cid10_folder:
            cid10_dbf = Path(temp_zip_extract_folder) / CID10_DBF_FILENAME
            cid10_csv = Path(csv_ibge_cid10_folder) / CID10_CSV_FILENAME
            if cid10_dbf.is_file():
                try:
                    Path(csv_ibge_cid10_folder).mkdir(parents=True, exist_ok=True)
                    DBFConverter.to_csv(cid10_dbf, cid10_csv)
                except (FileNotFoundError, Exception) as e:
                    print(f"Error converting {CID10_DBF_FILENAME} to {CID10_CSV_FILENAME}: {e}")

    def process_cih(
        self,
        temp_zip_folder: str | None = None,
        temp_zip_extract_folder: str | None = None,
    ) -> None:
        """
        Download TAB_CIH.zip to the zip folder and extract it to the extract folder.

        Args:
            temp_zip_folder: Folder where TAB_CIH.zip will be downloaded.
            temp_zip_extract_folder: Destination folder for extracted contents.
        """
        if temp_zip_folder:
            cih_service = DatasusCIHService(
                ftp_url=self._ftp_url,
                download_folder=temp_zip_folder,
            )
            cih_service.download()
        if temp_zip_folder and temp_zip_extract_folder:
            cih_zip = Path(temp_zip_folder) / CIH_ZIP_FILENAME
            if cih_zip.is_file():
                try:
                    ZipConverter.extract(cih_zip, temp_zip_extract_folder)
                except (FileNotFoundError, Exception) as e:
                    print(f"Error extracting {CIH_ZIP_FILENAME}: {e}")

    def process_ibge(
        self,
        temp_zip_folder: str | None = None,
        temp_zip_extract_folder: str | None = None,
        csv_ibge_municipios_folder: str | None = None,
        csv_ibge_uf_folder: str | None = None,
    ) -> None:
        """
        Run IBGE pipeline: download TAB_POP.zip, extract ZIPs, convert br_municip.cnv to MUNICIPIOS.CSV and br_uf.cnv to UF.CSV.

        Args:
            temp_zip_folder: Folder where IBGE ZIP (TAB_POP.zip) is downloaded.
            temp_zip_extract_folder: Destination folder for extracted ZIP contents.
            csv_ibge_municipios_folder: Folder where MUNICIPIOS.CSV will be written.
            csv_ibge_uf_folder: Folder where UF.CSV will be written.
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
        if temp_zip_extract_folder and csv_ibge_municipios_folder:
            cnv_municip_path = Path(temp_zip_extract_folder) / CNV_MUNICIP_REL_PATH
            municipios_csv_path = Path(csv_ibge_municipios_folder) / MUNICIPIOS_CSV_FILENAME
            if cnv_municip_path.is_file():
                try:
                    Path(csv_ibge_municipios_folder).mkdir(parents=True, exist_ok=True)
                    CNVConverter.to_csv(
                        cnv_municip_path,
                        municipios_csv_path,
                        CNVMunicipioSchema(),
                        encoding="latin-1",
                    )
                except (FileNotFoundError, Exception) as e:
                    print(f"Error converting {cnv_municip_path.name} to {MUNICIPIOS_CSV_FILENAME}: {e}")
        if temp_zip_extract_folder and csv_ibge_uf_folder:
            cnv_uf_path = Path(temp_zip_extract_folder) / CNV_UF_REL_PATH
            uf_csv_path = Path(csv_ibge_uf_folder) / UF_CSV_FILENAME
            if cnv_uf_path.is_file():
                try:
                    Path(csv_ibge_uf_folder).mkdir(parents=True, exist_ok=True)
                    CNVConverter.to_csv(
                        cnv_uf_path,
                        uf_csv_path,
                        CNVUFSchema(),
                        encoding="latin-1",
                    )
                except (FileNotFoundError, Exception) as e:
                    print(f"Error converting {cnv_uf_path.name} to {UF_CSV_FILENAME}: {e}")

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

    def process_datasus(self) -> None:
        """
        Run SIH download and converters (DBC -> DBF -> CSV), then process_ibge (download, extract, CNV -> MUNICIPIOS.CSV and UF.CSV).
        Reads all paths and options from the EnvLoader passed in the constructor.
        """
        from dtos import DatasusSIHDTO

        loader = self._loader
        if not loader.ftp_datasus:
            return
        params = DatasusSIHDTO(
            start_year=loader.start_year,
            start_month=loader.start_month,
            end_year=loader.end_year,
            end_month=loader.end_month,
            states=loader.states,
        )
        ignore_files_sih = self._ignore_files_sih_from_s3()
        service = self.create_sih_service(
            params,
            download_folder=loader.temp_dbc_path,
            ignore_files_sih=ignore_files_sih,
        )
        service.download()
        self.process_cih(
            temp_zip_folder=loader.temp_zip_folder,
            temp_zip_extract_folder=loader.temp_zip_extract_folder,
        )
        if loader.temp_dbc_path and loader.temp_dbf_path and loader.temp_csv_path:
            self.run_converters(
                loader.temp_dbc_path,
                loader.temp_dbf_path,
                loader.temp_csv_path,
                temp_zip_extract_folder=loader.temp_zip_extract_folder,
                csv_ibge_sigtap_folder=loader.csv_ibge_sigtap_folder,
                csv_ibge_cid10_folder=loader.csv_ibge_cid10_folder,
            )
        self.process_ibge(
            temp_zip_folder=loader.temp_zip_folder if loader.process_ibge else None,
            temp_zip_extract_folder=loader.temp_zip_extract_folder if loader.process_ibge else None,
            csv_ibge_municipios_folder=loader.csv_ibge_municipios_folder if loader.process_ibge else None,
            csv_ibge_uf_folder=loader.csv_ibge_uf_folder if loader.process_ibge else None,
        )
