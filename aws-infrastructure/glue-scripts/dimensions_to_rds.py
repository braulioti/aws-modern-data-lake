"""
Glue ETL job: read dimension data from Glue Data Catalog (crawler output), then load into RDS.
Only creates the tables and loads data if they do not exist. Adds the specified primary keys.
Uses --jdbc_url and --secret_arn job parameters.
"""
import json
import sys
import boto3
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql import types as T

# Resolve job parameters
args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "catalog_database",
        "jdbc_url",
        "secret_arn",
    ],
)
catalog_database = args["catalog_database"]
jdbc_url = args["jdbc_url"]
secret_arn = args["secret_arn"]

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# 1) Get username and password from Secrets Manager
client = boto3.client("secretsmanager")
secret = client.get_secret_value(SecretId=secret_arn)
secret_dict = json.loads(secret["SecretString"])
user = secret_dict.get("username")
password = secret_dict.get("password")

if not user or not password:
    raise ValueError("Secret missing username or password")

# Cast struct/array/map columns to string so JDBC write does not fail
def ensure_jdbc_safe(dataframe):
    cols = []
    for f in dataframe.schema.fields:
        if isinstance(f.dataType, (T.StructType, T.ArrayType, T.MapType)):
            cols.append(F.col(f.name).cast("string").alias(f.name))
        else:
            cols.append(F.col(f.name))
    return dataframe.select(cols)

def process_dimension(catalog_table, output_table, pk_column):
    print(f"--- Processing {catalog_table} -> {output_table} ---")
    try:
        # Check if table exists in RDS
        spark._jvm.Class.forName("org.postgresql.Driver")
        conn = spark._jvm.java.sql.DriverManager.getConnection(jdbc_url, user, password)
        db_meta = conn.getMetaData()
        rs = db_meta.getTables(None, None, output_table, None)
        table_exists = rs.next()
        
        if table_exists:
            print(f"Table {output_table} already exists in RDS. Skipping creation and load.")
            conn.close()
            return

        print(f"Table {output_table} does not exist. Reading from catalog...")
        dyf = glueContext.create_dynamic_frame.from_catalog(
            database=catalog_database,
            table_name=catalog_table,
        )
        df = dyf.toDF()
        
        if df.rdd.isEmpty():
            print(f"No data in catalog table {catalog_table}; skipping write.")
            conn.close()
            return

        df = ensure_jdbc_safe(df)
        
        print(f"Writing to RDS table: {output_table}")
        df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", output_table) \
            .option("user", user) \
            .option("password", password) \
            .option("driver", "org.postgresql.Driver") \
            .mode("overwrite") \
            .save()
            
        # Add primary key
        stmt = conn.createStatement()
        try:
            print(f"Adding primary key {pk_column} to {output_table}...")
            stmt.execute(f"ALTER TABLE {output_table} ADD PRIMARY KEY ({pk_column})")
            print(f"Successfully added primary key.")
        except Exception as e:
            print(f"Warning: Could not add primary key {pk_column} to {output_table}: {e}")
        finally:
            stmt.close()
            
        conn.close()
    except Exception as e:
        print(f"Error processing {catalog_table}: {e}")

# Dimensions configuration (catalog_table, output_table, pk_column)
# Note: catalog_table is usually the last segment of the S3 path (hyphens replaced with underscores)
dimensions = [
    {"catalog": "ibge_municipios", "output": "dim_ibge_municipios", "pk": "id"},
    {"catalog": "ibge_uf",         "output": "dim_ibge_uf",         "pk": "id"},
    {"catalog": "sigtap",          "output": "dim_sigtap",          "pk": "ip_cod"},
    {"catalog": "cid10",           "output": "dim_cid10",           "pk": "cid10"},
]

for dim in dimensions:
    process_dimension(dim["catalog"], dim["output"], dim["pk"])

job.commit()
