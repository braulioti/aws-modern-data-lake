# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-03-13

**AWS Modern Datalake** is a modern data lake architecture on AWS. It uses S3, Glue ETL, Athena, and BI tooling with raw, trusted, and refined layers. The Python module supports ingesting public health data from DATASUS (e.g. SIH — Hospital Information System) via FTP, configurable via environment variables.

### Feature

- Created basic structure to identify SIH DATASUS files for download.
- Created file download structure for SIH DATASUS files (skip existing files, download to temp folder, print status [OK]/[ERROR]).
- Created converters: DBCConverter (DBC to DBF) and DBFConverter (DBF to CSV); integrated into main pipeline with temp paths from env.
- Added Docker support: Dockerfile, docker-compose, env precedence over .env, default config values, unbuffered logs.
- Created ECR repository (sih-sus-repo) on AWS via CloudFormation using CDK stack SIHRepositoryStack.
- Added GitHub Actions workflow to build and push Docker image to ECR when a version tag (v*) is created.
- **Infrastructure (CDK):** DatalakeInfrastructureStack with VPC, S3 bucket, ECS Fargate cluster, Fargate task definition (CPU/memory configurable), IAM task role with S3 read/write permissions, CloudWatch Logs for the task; task environment variables include period, states, and AWS_S3_BUCKET (bucket name).
- **S3 integration:** Python `integration` package with `AWSIntegration` and `send_to_s3_bucket`; `AWS_S3_BUCKET` in EnvLoader and .env; pipeline uploads all converted CSV files to the S3 bucket (prefix `raw/sih/`) after DBC→DBF→CSV conversion.
- **Pipeline avoids re-download:** `AWSIntegration.list_s3_bucket` lists object keys in the bucket (optional prefix). `DatasusService`/`DatasusSIHService` gain an `ignore_files` property (array of file names to skip). In `main`, the list of CSVs in S3 (`raw/sih/`) is converted to `.dbc` names and passed as `ignore_files`, so the `.dbc` file is not downloaded when the corresponding CSV already exists in S3.
- **Glue ETL (CDK):** ETLGlueStack with Glue Data Catalog database for comma-separated CSV (`datalake_csv`), Glue Crawler reading from S3 prefix `raw/sih/`, CSV classifier (comma delimiter, header present), and IAM role with S3 read, CloudWatch Logs write, and Glue Data Catalog read/write permissions.
- **Municipalities table:** IBGE pipeline (TAB_POP.zip download, extract, CNV→CSV with CNVMunicipioSchema), MUNICIPIOS.CSV output; optional `PROCESS_IBGE` env to upload to S3 `raw/ibge-municipios/`; Glue Crawler for `raw/ibge-municipios/` populating `datalake_csv` with the municipalities table.
- **UF (Unidades Federativas):** IBGE pipeline also converts `br_uf.cnv` to UF.CSV (CNVUFSchema); upload to S3 `raw/ibge-uf/` when `PROCESS_IBGE` is enabled; Glue Crawler for `raw/ibge-uf/` populating `datalake_csv` with the UF table.
- **DatasusIntegration refactor:** `DatasusIntegration(EnvLoader)`; `process_datasus()` with no arguments (reads all paths and options from loader); `upload_ibge_csv_to_s3(loader)` moved to main as separate function; ignore list for SIH built inside integration from S3 (`raw/sih/`).
- **Converters naming:** folder-based methods renamed to include `_folder` (e.g. `DBCConverter.to_dbf_folder`, `DBFConverter.to_csv_folder`); `DBFConverter.to_csv` added for single-file DBF→CSV conversion.
- **CIH (Centro de Informação em Saúde):** `DatasusCIHService` downloads TAB_CIH.zip from `/dissemin/publicos/CIH/200801_201012/Auxiliar`; `process_cih` in DatasusIntegration downloads to zip folder and extracts to extract folder; runs before `run_converters` so extract contains auxiliary DBFs.
- **SIGTAP:** `run_converters` converts `extract/TB_SIGTAP.DBF` to CSV in `CSV_IBGE_SIGTAP_FOLDER` (env `CSV_IBGE_SIGTAP_FOLDER`, default `../tmp/csv_sigtap`); upload to S3 `raw/sigtap/`; Glue Crawler `sigtap-csv-crawler` for `raw/sigtap/` in `datalake_csv`.
- **CID10:** `run_converters` converts `extract/CID10.DBF` to CSV in `CSV_IBGE_CID10_FOLDER` (env `CSV_IBGE_CID10_FOLDER`, default `../tmp/csv_cid10`); upload to S3 `raw/cid10/`; Glue Crawler `cid10-csv-crawler` for `raw/cid10/` in `datalake_csv`.
- **Glue ETL Jobs to RDS:** Created `ETLGlueJobStack` with Glue Jobs to load data from Glue Data Catalog into PostgreSQL RDS dev instance via NETWORK connection. `sih-sus-job` loads SIH data (recreates table on each run). `dimensions-job` loads `dim_ibge_municipios`, `dim_ibge_uf`, `dim_sigtap` and `dim_cid10` only if they do not exist, and creates the primary key for each table.
- Created dimension tables in PostgreSQL RDS dev instance (see `database/schema.sql`).
- Call Glue ETL Jobs from ECS Fargate task.

### Bugfix

- **VPC / NAT Gateways:** Adjusted CDK for environments without NAT Gateways (to avoid cost). DatalakeInfrastructureStack keeps VPC with `natGateways(0)` without changing subnet configuration (to prevent CloudFormation update rollback). ETLGlueJobStack now uses **PUBLIC** subnets for the Glue connection (Glue has internet access and can reach RDS in public subnet). DatabaseStack now uses **PRIVATE_ISOLATED** subnets instead of `PRIVATE_WITH_EGRESS`, so the private RDS stack works when the VPC has only Public and Isolated subnets. Fixes validation error "There are no 'Private' subnet groups in this VPC". S3 Gateway Endpoint is not created by CDK (to avoid UPDATE_ROLLBACK due to export conflicts); create it manually in the VPC so Glue jobs can reach S3 (see README).

### Documentation

- Added README section "Architectural Model" with architecture diagram image (docs/architecture.png).
- Updated architecture design documentation.
- Created data dictionary for SIH/SUS (AIH Reduzida) at docs/dicionario-dados/DD_SIH.md.
