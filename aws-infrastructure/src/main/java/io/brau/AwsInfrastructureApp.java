package io.brau;

import software.amazon.awscdk.App;
import software.amazon.awscdk.Environment;
import software.amazon.awscdk.StackProps;
import software.constructs.Construct;

public class AwsInfrastructureApp {
    public static void main(final String[] args) {
        App app = new App();

        String account = getContextOrEnv(app, "account", "CDK_DEFAULT_ACCOUNT");
        String region = getContextOrEnv(app, "region", "CDK_DEFAULT_REGION");

        StackProps.Builder stackPropsBuilder = StackProps.builder();
        if (account != null && !account.isBlank() && region != null && !region.isBlank()) {
            stackPropsBuilder.env(Environment.builder()
                    .account(account)
                    .region(region)
                    .build());
        }

        StackProps stackProps = stackPropsBuilder.build();
        SIHRepositoryStack repoStack = new SIHRepositoryStack(app, "SIHRepositoryStack", stackProps);
        DatalakeInfrastructureStack datalakeStack = new DatalakeInfrastructureStack(app, "DatalakeInfrastructureStack", stackProps, repoStack.getRepository());
        new DatabaseStack(app, "DatabaseStack", stackProps, datalakeStack.getVpc());
        DatabasePublicStack databasePublicStack = new DatabasePublicStack(app, "DatabasePublicStack", stackProps, datalakeStack.getVpc());
        new ETLGlueStack(app, "ETLGlueStack", stackProps, datalakeStack.getBucket());
        new ETLGlueJobStack(app, "ETLGlueJobStack", stackProps, datalakeStack.getBucket(),
                datalakeStack.getVpc(), databasePublicStack.getInstance(), databasePublicStack.getSecretArn(),
                databasePublicStack.getGlueSecurityGroup());

        app.synth();
    }

    private static String getContextOrEnv(Construct construct, String contextKey, String envVar) {
        Object ctx = construct.getNode().tryGetContext(contextKey);
        if (ctx != null && !ctx.toString().isBlank()) {
            return ctx.toString();
        }
        String env = System.getenv(envVar);
        return (env != null && !env.isBlank()) ? env : null;
    }
}

