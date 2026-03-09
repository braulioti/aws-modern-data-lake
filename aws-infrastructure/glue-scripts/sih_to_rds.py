"""
Glue ETL job: read SIH data from Glue Data Catalog (crawler output), then load into RDS table st_sih.
Drops st_sih if it exists before creating and loading, so the table is recreated on each run.
Uses --jdbc_url and --secret_arn job parameters (no Glue JDBC connection needed).
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

# Resolve job parameters (set by CDK or job configuration)
args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "catalog_database",
        "catalog_table",
        "jdbc_url",
        "secret_arn",
        "output_table",
    ],
)
catalog_database = args["catalog_database"]
catalog_table = args["catalog_table"]
jdbc_url = args["jdbc_url"]
secret_arn = args["secret_arn"]
output_table = args["output_table"]

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# 1) Read SIH data from Glue Data Catalog (table populated by SIH crawler).
# If you get EntityNotFoundException: run the SIH crawler (sih-sus-csv-crawler) first, then set
# --catalog_table to the table name shown in Glue Console > Databases > datalake_csv > Tables (often "sih").
dyf = glueContext.create_dynamic_frame.from_catalog(
    database=catalog_database,
    table_name=catalog_table,
)
df = dyf.toDF()

if df.rdd.isEmpty():
    print("No data in catalog table; skipping write.")
    job.commit()
    sys.exit(0)

# 1b) Cast struct/array/map columns to string so JDBC write does not fail (JDBC has no type for complex types)
def ensure_jdbc_safe(dataframe):
    cols = []
    for f in dataframe.schema.fields:
        if isinstance(f.dataType, (T.StructType, T.ArrayType, T.MapType)):
            cols.append(F.col(f.name).cast("string").alias(f.name))
        else:
            cols.append(F.col(f.name))
    return dataframe.select(cols)

df = ensure_jdbc_safe(df)

# 2) Get username and password from Secrets Manager (job role must have secretsmanager:GetSecretValue)
client = boto3.client("secretsmanager")
secret = client.get_secret_value(SecretId=secret_arn)
secret_dict = json.loads(secret["SecretString"])
user = secret_dict.get("username")
password = secret_dict.get("password")
if not user or not password:
    raise ValueError("Secret missing username or password")

# 3) Drop output table if it exists (then we will create it on write)
# Use JVM JDBC (PostgreSQL driver is on Glue classpath) to run DROP TABLE
try:
    spark._jvm.Class.forName("org.postgresql.Driver")
    conn = spark._jvm.java.sql.DriverManager.getConnection(jdbc_url, user, password)
    stmt = conn.createStatement()
    stmt.execute("DROP TABLE IF EXISTS " + output_table + " CASCADE")
    stmt.close()
    conn.close()
    print("Dropped table if existed:", output_table)
except Exception as e:
    print("Drop table (optional):", e)

# 4) Write DataFrame to RDS (table will be created by Spark JDBC if not exists)
# Map Spark types to PostgreSQL; use overwrite to replace table
df.write \
    .format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", output_table) \
    .option("user", user) \
    .option("password", password) \
    .option("driver", "org.postgresql.Driver") \
    .mode("overwrite") \
    .save()

print("Written to RDS table:", output_table)
job.commit()
