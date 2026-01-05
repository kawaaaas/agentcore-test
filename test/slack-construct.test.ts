import { Template } from "aws-cdk-lib/assertions";
import * as cdk from "aws-cdk-lib/core";
import { SlackConstruct } from "../lib/constructs/notification/slack-construct";

describe("SlackConstruct", () => {
  test("Slack Construct が正常に作成される", () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, "TestStack");

    const slackConstruct = new SlackConstruct(stack, "SlackConstruct", {
      agentRuntimeFunctionName: "test-runtime-function",
    });

    const template = Template.fromStack(stack);

    // Construct が正常に作成されることを確認
    expect(template.toJSON()).toBeDefined();
    expect(slackConstruct.api).toBeDefined();
    expect(slackConstruct.webhookFunction).toBeDefined();
    expect(slackConstruct.messageTable).toBeDefined();
    expect(slackConstruct.signingSecret).toBeDefined();
    expect(slackConstruct.webhookUrl).toBeDefined();
  });

  test("API Gateway が作成される", () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, "TestStack");

    new SlackConstruct(stack, "SlackConstruct", {
      agentRuntimeFunctionName: "test-runtime-function",
    });

    const template = Template.fromStack(stack);
    const resources = template.toJSON().Resources;

    // API Gateway が作成されることを確認
    const apiResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::ApiGateway::RestApi"
    );
    expect(apiResources.length).toBe(1);
    expect((apiResources[0] as any).Properties.Name).toBe("slack-webhook-api");

    // Deployment が作成されることを確認
    const deploymentResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::ApiGateway::Deployment"
    );
    expect(deploymentResources.length).toBeGreaterThan(0);

    // Stage が作成されることを確認
    const stageResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::ApiGateway::Stage"
    );
    expect(stageResources.length).toBe(1);
    expect((stageResources[0] as any).Properties.StageName).toBe("prod");
  });

  test("Lambda 関数が作成される", () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, "TestStack");

    new SlackConstruct(stack, "SlackConstruct", {
      agentRuntimeFunctionName: "test-runtime-function",
    });

    const template = Template.fromStack(stack);
    const resources = template.toJSON().Resources;

    // Lambda 関数が作成されることを確認
    const lambdaResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::Lambda::Function"
    );
    expect(lambdaResources.length).toBe(1);

    const lambdaFunction = lambdaResources[0] as any;
    expect(lambdaFunction.Properties.FunctionName).toBe("slack-webhook");
    expect(lambdaFunction.Properties.Runtime).toBe("nodejs20.x");
    expect(lambdaFunction.Properties.Timeout).toBe(10);
    expect(lambdaFunction.Properties.Environment.Variables).toMatchObject({
      AGENTCORE_RUNTIME_FUNCTION_NAME: "test-runtime-function",
    });
  });

  test("DynamoDB テーブルが作成される", () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, "TestStack");

    new SlackConstruct(stack, "SlackConstruct", {
      agentRuntimeFunctionName: "test-runtime-function",
    });

    const template = Template.fromStack(stack);
    const resources = template.toJSON().Resources;

    // DynamoDB テーブルが作成されることを確認
    const tableResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::DynamoDB::GlobalTable"
    );
    expect(tableResources.length).toBe(1);

    const table = tableResources[0] as any;
    expect(table.Properties.TableName).toBe("slack-message-table");
    expect(table.Properties.KeySchema).toContainEqual({
      AttributeName: "session_id",
      KeyType: "HASH",
    });
  });

  test("Secrets Manager が作成される", () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, "TestStack");

    new SlackConstruct(stack, "SlackConstruct", {
      agentRuntimeFunctionName: "test-runtime-function",
    });

    const template = Template.fromStack(stack);
    const resources = template.toJSON().Resources;

    // Secrets Manager が作成されることを確認
    const secretResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::SecretsManager::Secret"
    );
    expect(secretResources.length).toBe(1);

    const secret = secretResources[0] as any;
    expect(secret.Properties.Name).toBe("slack-signing-secret");
    expect(secret.Properties.Description).toBe(
      "Slack Signing Secret for webhook verification"
    );
  });

  test("IAM ポリシーが正しく設定される", () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, "TestStack");

    new SlackConstruct(stack, "SlackConstruct", {
      agentRuntimeFunctionName: "test-runtime-function",
    });

    const template = Template.fromStack(stack);
    const resources = template.toJSON().Resources;

    // Lambda の IAM ロールが作成されることを確認
    const roleResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::IAM::Role"
    );
    expect(roleResources.length).toBeGreaterThan(0);

    // Lambda Invoke 権限が付与されることを確認
    const policyResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::IAM::Policy"
    );
    const hasLambdaInvokePermission = policyResources.some((policy: any) => {
      const statements = policy.Properties?.PolicyDocument?.Statement || [];
      return statements.some(
        (stmt: any) =>
          stmt.Action === "lambda:InvokeFunction" ||
          (Array.isArray(stmt.Action) &&
            stmt.Action.includes("lambda:InvokeFunction"))
      );
    });
    expect(hasLambdaInvokePermission).toBe(true);
  });

  test("プレフィックス付きでリソースが作成される", () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, "TestStack");

    new SlackConstruct(stack, "SlackConstruct", {
      agentRuntimeFunctionName: "test-runtime-function",
      prefix: "dev",
    });

    const template = Template.fromStack(stack);
    const resources = template.toJSON().Resources;

    // プレフィックス付きのリソース名が使用されることを確認
    const apiResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::ApiGateway::RestApi"
    );
    expect((apiResources[0] as any).Properties.Name).toBe(
      "dev-slack-webhook-api"
    );

    const lambdaResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::Lambda::Function"
    );
    expect((lambdaResources[0] as any).Properties.FunctionName).toBe(
      "dev-slack-webhook"
    );

    const tableResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::DynamoDB::GlobalTable"
    );
    expect((tableResources[0] as any).Properties.TableName).toBe(
      "dev-slack-message-table"
    );

    const secretResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::SecretsManager::Secret"
    );
    expect((secretResources[0] as any).Properties.Name).toBe(
      "dev-slack-signing-secret"
    );
  });
});
