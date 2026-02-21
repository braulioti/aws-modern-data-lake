"""
Script that reads the .env file and uses the FTP_DATASUS attribute.
"""
from config import EnvLoader
from dtos import DatasusSIHDTO
from services.datasus import DatasusSIHService


def main() -> None:
    loader = EnvLoader()

    if not loader.load():
        print(f"Warning: .env file not found at {loader.env_path}")
        print("Create a .env file with the FTP_DATASUS attribute (see .env.example)")
        return

    if not loader.ftp_datasus:
        print("Warning: FTP_DATASUS is not defined in .env")
    else:
        print(f"FTP_DATASUS: {loader.ftp_datasus}")

    sih_dto = DatasusSIHDTO(
        start_year=loader.start_year,
        start_month=loader.start_month,
        end_year=loader.end_year,
        end_month=loader.end_month,
        states=loader.states,
    )

    if loader.ftp_datasus:
        datasus_sih_service = DatasusSIHService(
            loader.ftp_datasus,
            params=sih_dto,
            download_folder=loader.temp_download_path,
        )
        datasus_sih_service.download()


if __name__ == "__main__":
    main()
