# Changelog

All notable changes to this project will be documented in this file.

## Project

**AWS Modern Datalake** is a modern data lake architecture on AWS. It uses S3, Glue ETL, Athena, and BI tooling with raw, trusted, and refined layers. The Python module supports ingesting public health data from DATASUS (e.g. SIH — Hospital Information System) via FTP, configurable via environment variables.

## [0.1.0] - 2026-02-21

### Feature

- Created basic structure to identify SIH DATASUS files for download.
- Created file download structure for SIH DATASUS files (skip existing files, download to temp folder, print status [OK]/[ERROR]).
- Created converters: DBCConverter (DBC to DBF) and DBFConverter (DBF to CSV); integrated into main pipeline with temp paths from env.
- Added Docker support: Dockerfile, docker-compose, env precedence over .env, default config values, unbuffered logs.
- Created ECR repository (sih-sus-repo) on AWS via CloudFormation using CDK stack DatalakeInfrastructureStack.
- Added GitHub Actions workflow to build and push Docker image to ECR when a version tag (v*) is created.
