package io.brau;

import java.util.List;
import java.util.Map;

import software.constructs.Construct;
import software.amazon.awscdk.Stack;
import software.amazon.awscdk.StackProps;
import software.amazon.awscdk.services.s3.assets.Asset;
import software.amazon.awscdk.services.ec2.IVpc;
import software.amazon.awscdk.services.ec2.ISecurityGroup;
import software.amazon.awscdk.services.ec2.ISubnet;
import software.amazon.awscdk.services.ec2.SubnetSelection;
import software.amazon.awscdk.services.ec2.SubnetType;
import software.amazon.awscdk.services.glue.CfnConnection;
import software.amazon.awscdk.services.glue.CfnJob;
import software.amazon.awscdk.services.iam.Effect;
import software.amazon.awscdk.services.iam.PolicyStatement;
import software.amazon.awscdk.services.iam.ServicePrincipal;
import software.amazon.awscdk.services.iam.Role;
import software.amazon.awscdk.services.rds.IDatabaseInstance;
import software.amazon.awscdk.services.s3.IBucket;

/**
 * Stack that creates AWS Glue ETL Jobs for the data lake pipeline.
 * Includes a job that reads SIH data from the Glue Data Catalog (crawler) and loads it into RDS dev (st_sih).
 * Depends on {@link DatalakeInfrastructureStack} for the S3 bucket and {@link DatabasePublicStack} for the RDS dev instance.
 */
public class ETLGlueJobStack extends Stack {

    /** Name of the SIH-SUS Glue ETL job. */
    public static final String SIH_SUS_JOB_NAME = "sih-sus-job";

    /** Glue catalog database (same as ETLGlueStack). */
    private static final String GLUE_DATABASE_NAME = "datalake_csv";
    /** Default catalog table for SIH. Crawler on path raw/sih/ creates a table named "sih" (last path segment). */
    private static final String DEFAULT_SIH_CATALOG_TABLE = "sih";
    /** RDS output table name. */
    private static final String OUTPUT_TABLE_ST_SIH = "st_sih";

    private final IBucket dataLakeBucket;

    public ETLGlueJobStack(final Construct scope, final String id, final IBucket dataLakeBucket) {
        this(scope, id, null, dataLakeBucket, null, null, null, null);
    }

    public ETLGlueJobStack(
            final Construct scope,
            final String id,
            final StackProps props,
            final IBucket dataLakeBucket,
            final IVpc vpc,
            final IDatabaseInstance rdsDevInstance,
            final String rdsDevSecretArn,
            final ISecurityGroup glueSecurityGroup) {
        super(scope, id, props);
        this.dataLakeBucket = dataLakeBucket;

        if (vpc == null || rdsDevInstance == null || rdsDevSecretArn == null || glueSecurityGroup == null) {
            return;
        }

        // Glue NETWORK connection: job runs in VPC (subnet + SG) to reach RDS; script gets JDBC from job params + Secrets Manager
        String connectionName = "rds-datalake-dev-network";
        String jdbcUrl = "jdbc:postgresql://" + rdsDevInstance.getDbInstanceEndpointAddress() + ":"
                + rdsDevInstance.getDbInstanceEndpointPort() + "/datalake";
        // Use PUBLIC subnets (no NAT cost); Glue has internet and can reach RDS in public subnet
        var selectedSubnets = vpc.selectSubnets(SubnetSelection.builder()
                .subnetType(SubnetType.PUBLIC)
                .build());
        List<String> subnetIds = selectedSubnets.getSubnetIds();
        ISubnet firstSubnet = selectedSubnets.getSubnets().get(0);
        String availabilityZone = firstSubnet.getAvailabilityZone();

        CfnConnection.Builder.create(this, "GlueRdsDevNetworkConnection")
                .catalogId(getAccount())
                .connectionInput(CfnConnection.ConnectionInputProperty.builder()
                        .connectionType("NETWORK")
                        .name(connectionName)
                        .physicalConnectionRequirements(CfnConnection.PhysicalConnectionRequirementsProperty.builder()
                                .availabilityZone(availabilityZone)
                                .subnetId(subnetIds.get(0))
                                .securityGroupIdList(List.of(glueSecurityGroup.getSecurityGroupId()))
                                .build())
                        .build())
                .build();

        // IAM role for the Glue job
        Role jobRole = Role.Builder.create(this, "GlueSihJobRole")
                .assumedBy(new ServicePrincipal("glue.amazonaws.com"))
                .build();
        dataLakeBucket.grantRead(jobRole);
        String catalogArn = "arn:aws:glue:" + getRegion() + ":" + getAccount() + ":catalog";
        String databaseArn = "arn:aws:glue:" + getRegion() + ":" + getAccount() + ":database/" + GLUE_DATABASE_NAME;
        String tableArn = "arn:aws:glue:" + getRegion() + ":" + getAccount() + ":table/" + GLUE_DATABASE_NAME + "/*";
        jobRole.addToPrincipalPolicy(PolicyStatement.Builder.create()
                .effect(Effect.ALLOW)
                .actions(List.of(
                        "glue:GetTable", "glue:GetTables",
                        "glue:GetDatabase", "glue:GetDatabases",
                        "glue:GetPartition", "glue:GetPartitions"))
                .resources(List.of(catalogArn, databaseArn, tableArn))
                .build());
        jobRole.addToPrincipalPolicy(PolicyStatement.Builder.create()
                .effect(Effect.ALLOW)
                .actions(List.of("glue:GetConnection"))
                .resources(List.of(
                        catalogArn,
                        "arn:aws:glue:" + getRegion() + ":" + getAccount() + ":connection/" + connectionName))
                .build());
        jobRole.addToPrincipalPolicy(PolicyStatement.Builder.create()
                .effect(Effect.ALLOW)
                .actions(List.of("secretsmanager:GetSecretValue"))
                .resources(List.of(rdsDevSecretArn))
                .build());
        String glueLogArn = "arn:aws:logs:" + getRegion() + ":" + getAccount() + ":log-group:/aws-glue/jobs/*";
        jobRole.addToPrincipalPolicy(PolicyStatement.Builder.create()
                .effect(Effect.ALLOW)
                .actions(List.of("logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"))
                .resources(List.of(glueLogArn))
                .build());
        // EC2 describe + ENI actions required by Glue when running in VPC
        jobRole.addToPrincipalPolicy(PolicyStatement.Builder.create()
                .effect(Effect.ALLOW)
                .actions(List.of(
                        "ec2:DescribeSubnets",
                        "ec2:DescribeVpcs",
                        "ec2:DescribeSecurityGroups",
                        "ec2:DescribeNetworkInterfaces",
                        "ec2:DescribeVpcEndpoints",
                        "ec2:DescribeRouteTables",
                        "ec2:CreateNetworkInterface",
                        "ec2:DeleteNetworkInterface",
                        "ec2:CreateTags",
                        "ec2:DeleteTags",
                        "ec2:DescribeNetworkInterfaceAttribute"))
                .resources(List.of("*"))
                .build());

        // Script asset (glue-scripts/sih_to_rds.py)
        Asset scriptAsset = Asset.Builder.create(this, "SihToRdsScript")
                .path("glue-scripts/sih_to_rds.py")
                .build();
        scriptAsset.grantRead(jobRole);
        String scriptLocation = "s3://" + scriptAsset.getS3BucketName() + "/" + scriptAsset.getS3ObjectKey();

        // Glue ETL job (SIH)
        CfnJob.Builder.create(this, "SihToRdsJob")
                .name(SIH_SUS_JOB_NAME)
                .role(jobRole.getRoleArn())
                .command(CfnJob.JobCommandProperty.builder()
                        .name("glueetl")
                        .scriptLocation(scriptLocation)
                        .pythonVersion("3")
                        .build())
                .defaultArguments(Map.of(
                        "--job-bookmark-option", "job-bookmark-disable",
                        "--catalog_database", GLUE_DATABASE_NAME,
                        "--catalog_table", DEFAULT_SIH_CATALOG_TABLE,
                        "--jdbc_url", jdbcUrl,
                        "--secret_arn", rdsDevSecretArn,
                        "--output_table", OUTPUT_TABLE_ST_SIH))
                .connections(CfnJob.ConnectionsListProperty.builder()
                        .connections(List.of(connectionName))
                        .build())
                .glueVersion("4.0")
                .workerType("G.1X")
                .numberOfWorkers(2)
                .build();

        // Script asset (glue-scripts/dimensions_to_rds.py)
        Asset dimensionsScriptAsset = Asset.Builder.create(this, "DimensionsToRdsScript")
                .path("glue-scripts/dimensions_to_rds.py")
                .build();
        dimensionsScriptAsset.grantRead(jobRole);
        String dimensionsScriptLocation = "s3://" + dimensionsScriptAsset.getS3BucketName() + "/" + dimensionsScriptAsset.getS3ObjectKey();

        // Glue ETL job (Dimensions)
        CfnJob.Builder.create(this, "DimensionsToRdsJob")
                .name("dimensions-job")
                .role(jobRole.getRoleArn())
                .command(CfnJob.JobCommandProperty.builder()
                        .name("glueetl")
                        .scriptLocation(dimensionsScriptLocation)
                        .pythonVersion("3")
                        .build())
                .defaultArguments(Map.of(
                        "--job-bookmark-option", "job-bookmark-disable",
                        "--catalog_database", GLUE_DATABASE_NAME,
                        "--jdbc_url", jdbcUrl,
                        "--secret_arn", rdsDevSecretArn))
                .connections(CfnJob.ConnectionsListProperty.builder()
                        .connections(List.of(connectionName))
                        .build())
                .glueVersion("4.0")
                .workerType("G.1X")
                .numberOfWorkers(2)
                .build();
    }

    /** Data lake S3 bucket (from DatalakeInfrastructureStack). */
    public IBucket getDataLakeBucket() {
        return dataLakeBucket;
    }
}
