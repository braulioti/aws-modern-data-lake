# Dicionário de Dados – SIH/SUS (AIH Reduzida)

Dicionário de dados completo dos campos do Sistema de Informações Hospitalares do SUS (SIH/SUS), arquivo de AIH Reduzida.

---

## Identificação da competência

| Campo     | Descrição           |
| --------- | ------------------- |
| ANO_CMPT  | Ano da competência  |
| MES_CMPT  | Mês da competência  |

## Identificação geográfica

| Campo     | Descrição                           |
| --------- | ----------------------------------- |
| UF_ZI     | Unidade da federação da internação  |
| MUNIC_RES | Município de residência             |
| MUNIC_MOV | Município do hospital               |

## Identificação da AIH

| Campo    | Descrição    |
| -------- | ------------ |
| N_AIH    | Número da AIH |
| IDENT    | Tipo da AIH   |
| GESTAO   | Tipo de gestão |
| COD_IDADE | Código da idade |
| IDADE    | Idade do paciente |
| DIAS_PERM | Dias de permanência |
| MORTE    | Indicador de óbito |

## Dados do estabelecimento

| Campo  | Descrição                              |
| ------ | -------------------------------------- |
| CNES   | Código do estabelecimento de saúde     |
| NAT_JUR | Natureza jurídica                     |
| REGCT  | Regime de contratação                  |

## Dados do paciente

| Campo     | Descrição      |
| --------- | -------------- |
| SEXO      | Sexo           |
| RACA_COR  | Raça/cor       |
| NACIONAL  | Nacionalidade   |
| NUM_FILHOS | Número de filhos |

## Datas da internação

| Campo    | Descrição          |
| -------- | ------------------ |
| DT_INTER | Data de internação |
| DT_SAIDA | Data de saída      |

## Procedimentos

| Campo     | Descrição               |
| --------- | ----------------------- |
| PROC_REA  | Procedimento realizado  |
| PROC_SOLIC | Procedimento solicitado |
| PROC_AUT  | Procedimento autorizado |

## Diagnóstico

| Campo     | Descrição                        |
| --------- | -------------------------------- |
| DIAG_PRINC | Diagnóstico principal (CID10)   |
| DIAG_SECUN | Diagnóstico secundário          |

## Diagnósticos adicionais

| Campo   | Descrição               |
| ------- | ----------------------- |
| DIAGSEC1 | Diagnóstico secundário 1 |
| DIAGSEC2 | Diagnóstico secundário 2 |
| DIAGSEC3 | Diagnóstico secundário 3 |
| DIAGSEC4 | Diagnóstico secundário 4 |
| DIAGSEC5 | Diagnóstico secundário 5 |
| DIAGSEC6 | Diagnóstico secundário 6 |
| DIAGSEC7 | Diagnóstico secundário 7 |
| DIAGSEC8 | Diagnóstico secundário 8 |
| DIAGSEC9 | Diagnóstico secundário 9 |

## Tipo de diagnóstico adicional

| Campo    | Descrição                    |
| -------- | ---------------------------- |
| TPDISEC1 | Tipo diagnóstico secundário 1 |
| TPDISEC2 | Tipo diagnóstico secundário 2 |
| TPDISEC3 | Tipo diagnóstico secundário 3 |
| TPDISEC4 | Tipo diagnóstico secundário 4 |
| TPDISEC5 | Tipo diagnóstico secundário 5 |
| TPDISEC6 | Tipo diagnóstico secundário 6 |
| TPDISEC7 | Tipo diagnóstico secundário 7 |
| TPDISEC8 | Tipo diagnóstico secundário 8 |
| TPDISEC9 | Tipo diagnóstico secundário 9 |

## Informações obstétricas

| Campo     | Descrição      |
| --------- | -------------- |
| GESTAO    | Tipo de gestão |
| PARTO     | Tipo de parto  |
| NUM_FILHOS | Número de filhos |

## Características da internação

| Campo   | Descrição               |
| ------- | ----------------------- |
| CAR_INT | Caráter da internação   |
| MOTSAI  | Motivo da saída         |
| COMPLEX | Complexidade            |

## Valores financeiros

| Campo      | Descrição                  |
| ---------- | -------------------------- |
| VAL_SH     | Valor serviços hospitalares |
| VAL_SP     | Valor serviços profissionais |
| VAL_SADT   | Valor SADT                 |
| VAL_RN     | Valor recém-nascido       |
| VAL_ACOMP  | Valor acompanhante       |
| VAL_ORTP   | Valor órteses/próteses   |
| VAL_SANGUE | Valor sangue             |
| VAL_SADTSR | Valor SADT sem rateio    |
| VAL_TRANSP | Valor transporte         |
| VAL_OBSANG | Valor sangue obstétrico |
| VAL_PED1AC | Valor pediatria 1       |
| VAL_TOT    | Valor total              |

## Informações administrativas

| Campo   | Descrição                |
| ------- | ------------------------ |
| AUD_JUST | Justificativa auditoria |
| COD_CID | Código CID               |
| COD_PROC | Código procedimento     |

## Informações adicionais

| Campo      | Descrição            |
| ---------- | -------------------- |
| CEP        | CEP residência       |
| UTI_MES_TO | UTI mês total        |
| UTI_INT_TO | UTI internação total |
| UTI_MES_AN | UTI mês anterior    |
| UTI_INT_AN | UTI internação anterior |

## Campos de controle do sistema

| Campo       | Descrição                    |
| ----------- | ---------------------------- |
| MARCA_UTI   | Indicador de UTI             |
| MARCA_OBITO | Indicador de óbito           |
| MARCA_ALTA  | Indicador de alta            |
| DATASUS     | Campo reservado para DATASUS |
