# Changelog

All notable changes to this project will be documented in this file.

## [0.X.0] - 2026-02-21

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

### Documentation

- Added README section "Architectural Model" with architecture diagram image (docs/architecture.png).
- Updated architecture design documentation.
- Created data dictionary for SIH/SUS (AIH Reduzida) at docs/dicionario-dados/DD_SIH.md.
