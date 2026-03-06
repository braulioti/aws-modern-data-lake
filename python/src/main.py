"""
Script that reads the .env file and uses the FTP_DATASUS attribute.
"""
from pathlib import Path

from config import EnvLoader
from dtos import DatasusSIHDTO
from integration import AWSIntegration, DatasusIntegration


S3_RAW_SIH_PREFIX = "raw/sih/"
S3_RAW_IBGE_PREFIX = "raw/ibge-municipios/"


def files_already_in_s3(bucket: str | None) -> list[str]:
    """
    Lista CSVs em S3 (raw/sih/), troca a extensão para .dbc e retorna essa lista
    para ignore_files_sih. Assim não baixamos o .dbc se o CSV já existir no S3.
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


def upload_csv_to_s3(
    csv_path: str | None,
    bucket: str | None,
    prefix: str = S3_RAW_SIH_PREFIX,
) -> None:
    """Upload all CSV files from the given directory to the S3 bucket under the given prefix."""
    if not csv_path or not bucket:
        return
    csv_dir = Path(csv_path)
    if not csv_dir.is_dir():
        return
    aws = AWSIntegration()
    for csv_file in csv_dir.glob("*.csv"):
        key = f"{prefix}{csv_file.name}"
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
        ignore_files_sih = files_already_in_s3(loader.aws_s3_bucket)
        datasus = DatasusIntegration(loader.ftp_datasus)
        datasus.process_datasus(
            sih_dto,
            loader.temp_dbc_path,
            ignore_files_sih=ignore_files_sih,
            temp_dbf_path=loader.temp_dbf_path,
            temp_csv_path=loader.temp_csv_path,
            temp_zip_folder=loader.temp_zip_folder if loader.process_ibge else None,
            temp_zip_extract_folder=loader.temp_zip_extract_folder if loader.process_ibge else None,
            csv_ibge_folder=loader.csv_ibge_folder if loader.process_ibge else None,
        )
        upload_csv_to_s3(loader.temp_csv_path, loader.aws_s3_bucket)
        if loader.process_ibge:
            upload_csv_to_s3(
                loader.csv_ibge_folder,
                loader.aws_s3_bucket,
                prefix=S3_RAW_IBGE_PREFIX,
            )


if __name__ == "__main__":
    main()
