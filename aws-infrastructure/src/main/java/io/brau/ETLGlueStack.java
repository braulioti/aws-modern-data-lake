package io.brau;

import java.util.List;

import software.constructs.Construct;
import software.amazon.awscdk.Stack;
import software.amazon.awscdk.StackProps;
import software.amazon.awscdk.services.glue.CfnClassifier;
import software.amazon.awscdk.services.glue.CfnCrawler;
import software.amazon.awscdk.services.glue.CfnDatabase;
import software.amazon.awscdk.services.iam.Effect;
import software.amazon.awscdk.services.iam.PolicyStatement;
import software.amazon.awscdk.services.iam.ServicePrincipal;
import software.amazon.awscdk.services.iam.Role;
import software.amazon.awscdk.services.s3.IBucket;

/**
 * Stack that creates Glue resources for ETL: a Data Catalog database for CSV
 * and a crawler that reads CSV files (comma-separated) from the data lake S3 bucket.
 * Depends on {@link DatalakeInfrastructureStack} for the S3 bucket.
 */
public class ETLGlueStack extends Stack {

    private static final String GLUE_DATABASE_NAME = "datalake_csv";
    private static final String CRAWLER_NAME = "sih-sus-csv-crawler";
    private static final String MUNICIPIOS_CRAWLER_NAME = "municipios-csv-crawler";
    private static final String CRAWLER_ROLE_NAME = "datalake-glue-crawler-role";
    private static final String CSV_CLASSIFIER_NAME = "csv-comma";
    /** S3 prefix where SIH CSV files are stored. */
    private static final String CSV_S3_PREFIX = "raw/sih/";
    /** S3 prefix where IBGE CSV files are stored (e.g. MUNICIPIOS.CSV). */
    private static final String CSV_IBGE_S3_PREFIX = "raw/ibge/";

    public ETLGlueStack(final Construct scope, final String id, final IBucket dataLakeBucket) {
        this(scope, id, null, dataLakeBucket);
    }

    public ETLGlueStack(final Construct scope, final String id, final StackProps props, final IBucket dataLakeBucket) {
        super(scope, id, props);

        // Catalog (database) in Glue Data Catalog for CSV tables (SIH and IBGE e.g. municipalities)
        CfnDatabase.Builder.create(this, "CsvCatalog")
                .catalogId(getAccount())
                .databaseInput(CfnDatabase.DatabaseInputProperty.builder()
                        .name(GLUE_DATABASE_NAME)
                        .description("Catalog for comma-separated CSV files from S3 (SIH and IBGE)")
                        .build())
                .build();

        // CSV classifier with comma delimiter
        CfnClassifier.Builder.create(this, "CsvCommaClassifier")
                .csvClassifier(CfnClassifier.CsvClassifierProperty.builder()
                        .name(CSV_CLASSIFIER_NAME)
                        .delimiter(",")
                        .containsHeader("PRESENT")
                        .build())
                .build();

        // IAM role for the Glue Crawler to access S3 and write logs
        Role crawlerRole = Role.Builder.create(this, "GlueCrawlerRole")
                .roleName(CRAWLER_ROLE_NAME)
                .assumedBy(new ServicePrincipal("glue.amazonaws.com"))
                .build();
        dataLakeBucket.grantRead(crawlerRole);
        // Allow crawler to write to the default Glue crawler log group
        String glueLogGroupArn = "arn:aws:logs:" + getRegion() + ":" + getAccount() + ":log-group:/aws-glue/crawlers:*";
        crawlerRole.addToPrincipalPolicy(PolicyStatement.Builder.create()
                .effect(Effect.ALLOW)
                .actions(List.of("logs:CreateLogStream", "logs:PutLogEvents"))
                .resources(List.of(glueLogGroupArn))
                .build());
        // Allow crawler to read and write Glue Data Catalog (datalake_csv database and tables)
        String catalogArn = "arn:aws:glue:" + getRegion() + ":" + getAccount() + ":catalog";
        String databaseArn = "arn:aws:glue:" + getRegion() + ":" + getAccount() + ":database/" + GLUE_DATABASE_NAME;
        String tableArn = "arn:aws:glue:" + getRegion() + ":" + getAccount() + ":table/" + GLUE_DATABASE_NAME + "/*";
        crawlerRole.addToPrincipalPolicy(PolicyStatement.Builder.create()
                .effect(Effect.ALLOW)
                .actions(List.of(
                        "glue:GetDatabase", "glue:GetDatabases",
                        "glue:GetTable", "glue:GetTables",
                        "glue:CreateTable", "glue:UpdateTable",
                        "glue:GetPartition", "glue:GetPartitions",
                        "glue:CreatePartition", "glue:UpdatePartition",
                        "glue:BatchCreatePartition", "glue:BatchUpdatePartition"))
                .resources(List.of(catalogArn, databaseArn, tableArn))
                .build());

        // Crawler that reads SIH CSV files from S3 and populates the catalog
        String s3PathSih = "s3://" + dataLakeBucket.getBucketName() + "/" + CSV_S3_PREFIX;
        CfnCrawler.Builder.create(this, "CsvCrawler")
                .name(CRAWLER_NAME)
                .role(crawlerRole.getRoleArn())
                .databaseName(GLUE_DATABASE_NAME)
                .classifiers(List.of(CSV_CLASSIFIER_NAME))
                .targets(CfnCrawler.TargetsProperty.builder()
                        .s3Targets(List.of(CfnCrawler.S3TargetProperty.builder()
                                .path(s3PathSih)
                                .build()))
                        .build())
                .build();

        // Crawler that reads IBGE CSV files (e.g. MUNICIPIOS.CSV) from S3 into the same datalake_csv database
        String s3PathIbge = "s3://" + dataLakeBucket.getBucketName() + "/" + CSV_IBGE_S3_PREFIX;
        CfnCrawler.Builder.create(this, "MunicipiosCsvCrawler")
                .name(MUNICIPIOS_CRAWLER_NAME)
                .role(crawlerRole.getRoleArn())
                .databaseName(GLUE_DATABASE_NAME)
                .classifiers(List.of(CSV_CLASSIFIER_NAME))
                .targets(CfnCrawler.TargetsProperty.builder()
                        .s3Targets(List.of(CfnCrawler.S3TargetProperty.builder()
                                .path(s3PathIbge)
                                .build()))
                        .build())
                .build();
    }
}
