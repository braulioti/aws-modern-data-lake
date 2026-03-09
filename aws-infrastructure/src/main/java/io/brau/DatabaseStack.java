package io.brau;

import software.constructs.Construct;
import software.amazon.awscdk.Stack;
import software.amazon.awscdk.StackProps;
import software.amazon.awscdk.services.ec2.IVpc;
import software.amazon.awscdk.services.ec2.InstanceClass;
import software.amazon.awscdk.services.ec2.InstanceSize;
import software.amazon.awscdk.services.ec2.InstanceType;
import software.amazon.awscdk.services.ec2.SubnetSelection;
import software.amazon.awscdk.services.ec2.SubnetType;
import software.amazon.awscdk.services.rds.Credentials;
import software.amazon.awscdk.services.rds.CredentialsBaseOptions;
import software.amazon.awscdk.services.rds.DatabaseInstance;
import software.amazon.awscdk.services.rds.DatabaseInstanceEngine;
import software.amazon.awscdk.services.rds.PostgresEngineVersion;
import software.amazon.awscdk.services.rds.PostgresInstanceEngineProps;

/**
 * Stack that creates an RDS database instance in private subnets (VPC-only access).
 * For a publicly accessible dev instance, use {@link DatabasePublicStack} instead.
 * Depends on {@link DatalakeInfrastructureStack} for the VPC.
 */
public class DatabaseStack extends Stack {

    private static final String DB_INSTANCE_ID = "datalake-db";
    private static final String DB_NAME = "datalake";
    private static final String DB_USERNAME = "postgres";
    private static final String DB_SECRET_NAME = "datalake-db-credentials";

    public DatabaseStack(final Construct scope, final String id, final IVpc vpc) {
        this(scope, id, null, vpc);
    }

    public DatabaseStack(final Construct scope, final String id, final StackProps props, final IVpc vpc) {
        super(scope, id, props);

        Credentials credentials = Credentials.fromGeneratedSecret(DB_USERNAME, CredentialsBaseOptions.builder()
                .secretName(DB_SECRET_NAME)
                .build());

        DatabaseInstance.Builder.create(this, "DatalakeDatabase")
                .instanceIdentifier(DB_INSTANCE_ID)
                .engine(DatabaseInstanceEngine.postgres(PostgresInstanceEngineProps.builder()
                        .version(PostgresEngineVersion.VER_16_3)
                        .build()))
                .credentials(credentials)
                .databaseName(DB_NAME)
                .vpc(vpc)
                // Isolated subnets (no NAT); use DatabasePublicStack for dev if you need public RDS
                .vpcSubnets(SubnetSelection.builder().subnetType(SubnetType.PRIVATE_ISOLATED).build())
                .instanceType(InstanceType.of(InstanceClass.BURSTABLE3, InstanceSize.MICRO))
                .allocatedStorage(20)
                .publiclyAccessible(false)
                .build();
    }
}
