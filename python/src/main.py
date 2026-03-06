"""
Script that reads the .env file and uses the FTP_DATASUS attribute.
"""
from pathlib import Path

from config import EnvLoader
from integration import AWSIntegration, DatasusIntegration


S3_RAW_SIH_PREFIX = "raw/sih/"
S3_RAW_IBGE_MUNICIPIOS_PREFIX = "raw/ibge-municipios/"
S3_RAW_IBGE_UF_PREFIX = "raw/ibge-uf/"
S3_RAW_SIGTAP_PREFIX = "raw/sigtap/"
S3_RAW_CID10_PREFIX = "raw/cid10/"


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


def upload_ibge_csv_to_s3(loader: EnvLoader) -> None:
    """If process_ibge is enabled, upload IBGE municipalities and UF CSV folders to S3."""
    if not loader.process_ibge:
        return
    upload_csv_to_s3(
        loader.csv_ibge_municipios_folder,
        loader.aws_s3_bucket,
        prefix=S3_RAW_IBGE_MUNICIPIOS_PREFIX,
    )
    upload_csv_to_s3(
        loader.csv_ibge_uf_folder,
        loader.aws_s3_bucket,
        prefix=S3_RAW_IBGE_UF_PREFIX,
    )


def main() -> None:
    loader = EnvLoader()
    loader.load()

    print(f"FTP_DATASUS: {loader.ftp_datasus}")

    if loader.ftp_datasus:
        datasus = DatasusIntegration(loader)
        datasus.process_datasus()
        upload_csv_to_s3(loader.temp_csv_path, loader.aws_s3_bucket)
        upload_csv_to_s3(
            loader.csv_ibge_sigtap_folder,
            loader.aws_s3_bucket,
            prefix=S3_RAW_SIGTAP_PREFIX,
        )
        upload_csv_to_s3(
            loader.csv_ibge_cid10_folder,
            loader.aws_s3_bucket,
            prefix=S3_RAW_CID10_PREFIX,
        )
        upload_ibge_csv_to_s3(loader)


if __name__ == "__main__":
    main()
