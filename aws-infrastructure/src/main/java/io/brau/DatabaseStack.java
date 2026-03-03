package io.brau;

import software.constructs.Construct;
import software.amazon.awscdk.Stack;
import software.amazon.awscdk.StackProps;
import software.amazon.awscdk.services.ec2.IVpc;
import software.amazon.awscdk.services.ec2.InstanceClass;
import software.amazon.awscdk.services.ec2.InstanceSize;
import software.amazon.awscdk.services.ec2.InstanceType;
import software.amazon.awscdk.services.rds.Credentials;
import software.amazon.awscdk.services.rds.CredentialsBaseOptions;
import software.amazon.awscdk.services.rds.DatabaseInstance;
import software.amazon.awscdk.services.rds.DatabaseInstanceEngine;
import software.amazon.awscdk.services.rds.PostgresEngineVersion;
import software.amazon.awscdk.services.rds.PostgresInstanceEngineProps;

/**
 * Stack that creates an RDS database instance.
 * Depends on {@link DatalakeInfrastructureStack} for the VPC.
 */
public class DatabaseStack extends Stack {

    private static final String DB_INSTANCE_ID = "datalake-db";
    private static final String DB_NAME = "datalake";
    private static final String DB_USERNAME = "postgres";

    /**
     * WARNING: Do not use publiclyAccessible(true) in production.
     * Exposing the database to the internet is a security risk. For production,
     * keep the instance in private subnets and access via VPN, bastion, or
     * private connectivity (e.g. VPC peering, PrivateLink).
     */
    private static final boolean PUBLIC_ACCESS_FOR_DEV_ONLY = true;

    /** Secret name in AWS Secrets Manager for the DB password (never logged or shown in CloudFormation). */
    private static final String DB_SECRET_NAME = "datalake-db-credentials";

    public DatabaseStack(final Construct scope, final String id, final IVpc vpc) {
        this(scope, id, null, vpc);
    }

    public DatabaseStack(final Construct scope, final String id, final StackProps props, final IVpc vpc) {
        super(scope, id, props);

        // Only when PUBLIC_ACCESS_FOR_DEV_ONLY: random password in AWS Secrets Manager (never in CloudFormation/logs).
        Credentials credentials = PUBLIC_ACCESS_FOR_DEV_ONLY
                ? Credentials.fromGeneratedSecret(DB_USERNAME, CredentialsBaseOptions.builder()
                        .secretName(DB_SECRET_NAME)
                        .build())
                : Credentials.fromGeneratedSecret(DB_USERNAME);

        DatabaseInstance.Builder.create(this, "DatalakeDatabase")
                .instanceIdentifier(DB_INSTANCE_ID)
                .engine(DatabaseInstanceEngine.postgres(PostgresInstanceEngineProps.builder()
                        .version(PostgresEngineVersion.VER_16_3)
                        .build()))
                .credentials(credentials)
                .databaseName(DB_NAME)
                .vpc(vpc)
                .instanceType(InstanceType.of(InstanceClass.BURSTABLE3, InstanceSize.MICRO))
                .allocatedStorage(20)
                .publiclyAccessible(PUBLIC_ACCESS_FOR_DEV_ONLY)
                .build();
    }
}
