"""
City CNV schema: id, cod_ibge, municipio (fixed-width layout).
"""

from cnv_schemas.cnv_schema import CNVField, CNVSchema


class CNVCitySchema(CNVSchema):
    """
    CNV schema for city/municipality data: id, cod_ibge, municipio.
    """

    def __init__(self) -> None:
        super().__init__(
            [
                CNVField(pos_start=0, size=7, title="id", type="int"),
                CNVField(pos_start=9, size=6, title="cod_ibge", type="int"),
                CNVField(pos_start=16, size=43, title="municipio", type="string"),
            ]
        )
