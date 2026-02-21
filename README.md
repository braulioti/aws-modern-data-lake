# AWS Modern Datalake - Version: 1.0.0

[![X: @_brau_io](https://img.shields.io/badge/contact-@_brau_io-blue.svg?style=flat)](https://x.com/_brau_io)
[![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)

Modern data lake architecture on AWS featuring S3, Glue ETL, Athena analytics, and BI visualization following raw, trusted, and refined layers.

AWS Modern Datalake is created and maintained by [Bráulio Figueiredo](https://brau.io).

## Table of Contents

- [Technologies](#technologies)
- [SIH DATASUS DBC file structure](#sih-datasus-dbc-file-structure)
- [Versioning](#versioning)
- [Author](#author)

## Technologies

- Amazon AWS
- Python 3.10+

## SIH DATASUS DBC file structure

Files from the **SIH** (Sistema de Informações Hospitalares — Hospital Information System) on DATASUS FTP follow this naming pattern:

**`RD` + `UF` + `AAMM` + `.dbc`**

| Part | Description |
|------|-------------|
| **RD** | Fixed prefix for the SIH dataset |
| **UF** | Two-letter Brazilian state code (e.g. SP, RJ, MG) |
| **AAMM** | Reference period: **AA** = two-digit year, **MM** = two-digit month |

### Examples

| File | State | Period |
|------|-------|--------|
| `RDSP2301.dbc` | São Paulo | January 2023 |
| `RDRJ2301.dbc` | Rio de Janeiro | January 2023 |
| `RDMG2301.dbc` | Minas Gerais | January 2023 |

## Versioning

AWS Modern Datalake "Semantic Versioning" guidelines whenever possible.
Updates are numbered as follows:

`<major>.<minor>.<patch>`

Built on the following guidelines:

* Breaking compatibility with the previous version will be updated in "major"
* New implementations and features in "minor"
* Bug fixes in "patch"

For more information about SemVer, please visit http://semver.org.

## Author
- Email: braulio@braulioti.com.br
- X: https://x.com/_brau_io
- GitHub: https://github.com/braulioti
- Website: https://brau.io      
