package io.brau;

import software.constructs.Construct;
import software.amazon.awscdk.Stack;
import software.amazon.awscdk.StackProps;
import software.amazon.awscdk.services.ec2.CfnSecurityGroupIngress;
import software.amazon.awscdk.services.ec2.IVpc;
import software.amazon.awscdk.services.ec2.ISecurityGroup;
import software.amazon.awscdk.services.ec2.SecurityGroup;
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
import software.amazon.awscdk.services.rds.IDatabaseInstance;

/**
 * Stack that creates a publicly accessible RDS instance for development (datalake-db-dev).
 * Placed in public subnets so it can be reached from the internet. Not for production use.
 * Also creates a security group for Glue job access (to avoid cyclic dependency with ETLGlueJobStack).
 * Depends on {@link DatalakeInfrastructureStack} for the VPC.
 */
public class DatabasePublicStack extends Stack {

    private static final String DB_INSTANCE_ID = "datalake-db-dev";
    private static final String DB_NAME = "datalake";
    private static final String DB_USERNAME = "postgres";
    private static final String DB_SECRET_NAME = "datalake-db-dev-credentials";

    private final DatabaseInstance db;
    private final SecurityGroup glueAccessSg;

    public DatabasePublicStack(final Construct scope, final String id, final IVpc vpc) {
        this(scope, id, null, vpc);
    }

    public DatabasePublicStack(final Construct scope, final String id, final StackProps props, final IVpc vpc) {
        super(scope, id, props);

        Credentials credentials = Credentials.fromGeneratedSecret(DB_USERNAME, CredentialsBaseOptions.builder()
                .secretName(DB_SECRET_NAME)
                .build());

        this.db = DatabaseInstance.Builder.create(this, "DatalakeDatabaseDev")
                .instanceIdentifier(DB_INSTANCE_ID)
                .engine(DatabaseInstanceEngine.postgres(PostgresInstanceEngineProps.builder()
                        .version(PostgresEngineVersion.VER_16_3)
                        .build()))
                .credentials(credentials)
                .databaseName(DB_NAME)
                .vpc(vpc)
                .vpcSubnets(SubnetSelection.builder().subnetType(SubnetType.PUBLIC).build())
                .instanceType(InstanceType.of(InstanceClass.BURSTABLE3, InstanceSize.MICRO))
                .allocatedStorage(20)
                .publiclyAccessible(true)
                .build();

        this.db.getConnections().allowDefaultPortFromAnyIpv4("Allow PostgreSQL from internet (dev only)");

        // Security group for Glue job (created here to avoid cyclic dependency with ETLGlueJobStack)
        this.glueAccessSg = SecurityGroup.Builder.create(this, "GlueAccessSecurityGroup")
                .vpc(vpc)
                .description("Security group for Glue job connecting to RDS dev")
                .allowAllOutbound(true)
                .build();
        // Self-referencing rule as separate resource (required by Glue; inline rule would cause circular dependency with RDS rule)
        CfnSecurityGroupIngress.Builder.create(this, "GlueAccessSelfRefIngress")
                .groupId(this.glueAccessSg.getSecurityGroupId())
                .sourceSecurityGroupId(this.glueAccessSg.getSecurityGroupId())
                .ipProtocol("tcp")
                .fromPort(0)
                .toPort(65535)
                .build();
        this.db.getConnections().allowDefaultPortFrom(this.glueAccessSg, "Allow Glue job to RDS dev");
    }

    /** RDS instance (for Glue job connection and security group rules). */
    public IDatabaseInstance getInstance() {
        return this.db;
    }

    /** Secret ARN for RDS credentials (for Glue connection SECRET_ID). */
    public String getSecretArn() {
        return this.db.getSecret().getSecretArn();
    }

    /** Security group for Glue job connection (use in ETLGlueJobStack to avoid cyclic dependency). */
    public ISecurityGroup getGlueSecurityGroup() {
        return this.glueAccessSg;
    }
}
