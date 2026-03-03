"""
Script that reads the .env file and uses the FTP_DATASUS attribute.
"""
from pathlib import Path

from config import EnvLoader
from converter import DBCConverter, DBFConverter
from dtos import DatasusSIHDTO
from integration import AWSIntegration
from services.datasus import DatasusSIHService


S3_RAW_SIH_PREFIX = "raw/sih/"


def files_already_in_s3(bucket: str | None) -> list[str]:
    """
    Lista CSVs em S3 (raw/sih/), troca a extensão para .dbc e retorna essa lista
    para ignore_files. Assim não baixamos o .dbc se o CSV já existir no S3.
    Ex.: raw/sih/RDSP202501.csv no S3 -> retorna ["RDSP202501.dbc"] para ignorar.
    """
    if not bucket:
        return []
    aws = AWSIntegration()
    keys = aws.list_s3_bucket(bucket, prefix=S3_RAW_SIH_PREFIX)
    # Listagem do S3 (CSV) -> nomes .dbc para não baixar
    ignore_dbc: list[str] = []
    for key in keys:
        name = Path(key).name
        if name.endswith(".csv"):
            ignore_dbc.append(Path(name).with_suffix(".dbc").name)
    return ignore_dbc


def upload_csv_to_s3(csv_path: str | None, bucket: str | None) -> None:
    """Upload all CSV files from the given directory to the S3 bucket under raw/sih/."""
    if not csv_path or not bucket:
        return
    csv_dir = Path(csv_path)
    if not csv_dir.is_dir():
        return
    aws = AWSIntegration()
    for csv_file in csv_dir.glob("*.csv"):
        key = f"{S3_RAW_SIH_PREFIX}{csv_file.name}"
        uri = aws.send_to_s3_bucket(
            bucket, key, str(csv_file), content_type="text/csv"
        )
        print(f"Uploaded: {uri}")


def main() -> None:
    loader = EnvLoader()
    loader.load()

    print(f"FTP_DATASUS: {loader.ftp_datasus}")

    sih_dto = DatasusSIHDTO(
        start_year=loader.start_year,
        start_month=loader.start_month,
        end_year=loader.end_year,
        end_month=loader.end_month,
        states=loader.states,
    )

    if loader.ftp_datasus:
        ignore_files = files_already_in_s3(loader.aws_s3_bucket)
        datasus_sih_service = DatasusSIHService(
            loader.ftp_datasus,
            params=sih_dto,
            download_folder=loader.temp_dbc_path,
            ignore_files=ignore_files,
        )
        datasus_sih_service.download()

        if loader.temp_dbc_path and loader.temp_dbf_path:
            DBCConverter.to_dbf(loader.temp_dbc_path, loader.temp_dbf_path)

        if loader.temp_dbf_path and loader.temp_csv_path:
            DBFConverter.to_csv(loader.temp_dbf_path, loader.temp_csv_path)

        upload_csv_to_s3(loader.temp_csv_path, loader.aws_s3_bucket)


if __name__ == "__main__":
    main()
