import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as nodejs from "aws-cdk-lib/aws-lambda-nodejs";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";
import * as path from "node:path";

/**
 * SlackConstruct のプロパティ
 */
export interface SlackConstructProps {
  /**
   * AgentCore Runtime の関数名（必須）
   * Webhook Lambda から Runtime を呼び出すために使用
   */
  readonly agentRuntimeFunctionName: string;

  /**
   * Slack Signing Secret（オプション）
   * 指定しない場合は新しい Secret を作成
   */
  readonly slackSigningSecret?: secretsmanager.ISecret;

  /**
   * リソース名のプレフィックス（オプション）
   */
  readonly prefix?: string;
}

/**
 * Slack 連携を管理する Construct
 * - API Gateway: Slack からのインタラクションを受信する HTTPS エンドポイント
 * - Lambda: 署名検証と Runtime への通知
 * - DynamoDB: メッセージ状態管理
 * - Secrets Manager: Slack Signing Secret の管理
 *
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */
export class SlackConstruct extends Construct {
  /**
   * Slack Webhook 用 API Gateway
   */
  public readonly api: apigateway.RestApi;

  /**
   * Webhook Lambda 関数
   */
  public readonly webhookFunction: lambda.Function;

  /**
   * Slack メッセージレコード用 DynamoDB テーブル
   */
  public readonly messageTable: dynamodb.TableV2;

  /**
   * Slack Signing Secret
   */
  public readonly signingSecret: secretsmanager.ISecret;

  /**
   * Webhook エンドポイント URL
   */
  public readonly webhookUrl: string;

  constructor(scope: Construct, id: string, props: SlackConstructProps) {
    super(scope, id);

    const prefix = props.prefix ?? "";

    // Slack Signing Secret の設定
    // Requirements: 7.1, 7.2, 7.3
    this.signingSecret =
      props.slackSigningSecret ??
      new secretsmanager.Secret(this, "SlackSigningSecret", {
        secretName: prefix
          ? `${prefix}-slack-signing-secret`
          : "slack-signing-secret",
        description: "Slack Signing Secret for webhook verification",
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });

    // DynamoDB テーブルの作成
    // Requirements: 5.1, 5.2, 5.3
    this.messageTable = new dynamodb.TableV2(this, "SlackMessageTable", {
      tableName: prefix
        ? `${prefix}-slack-message-table`
        : "slack-message-table",
      partitionKey: {
        name: "session_id",
        type: dynamodb.AttributeType.STRING,
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Webhook Lambda 関数の作成
    // Requirements: 9.4
    this.webhookFunction = new nodejs.NodejsFunction(this, "WebhookFunction", {
      functionName: prefix ? `${prefix}-slack-webhook` : "slack-webhook",
      entry: path.join(__dirname, "../../../lambda/slack-webhook/handler.ts"),
      handler: "handler",
      runtime: lambda.Runtime.NODEJS_20_X,
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      environment: {
        SLACK_SIGNING_SECRET: this.signingSecret.secretArn,
        AGENTCORE_RUNTIME_FUNCTION_NAME: props.agentRuntimeFunctionName,
        MESSAGE_TABLE_NAME: this.messageTable.tableName,
      },
      description: "Slack Webhook handler for interaction events",
    });

    // Secrets Manager からの読み取り権限を付与
    this.signingSecret.grantRead(this.webhookFunction);

    // DynamoDB テーブルへの読み書き権限を付与
    this.messageTable.grantReadWriteData(this.webhookFunction);

    // AgentCore Runtime を呼び出す権限を付与
    this.webhookFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["lambda:InvokeFunction"],
        resources: [
          `arn:aws:lambda:${cdk.Stack.of(this).region}:${
            cdk.Stack.of(this).account
          }:function:${props.agentRuntimeFunctionName}`,
        ],
      })
    );

    // API Gateway の作成
    // Requirements: 9.1
    this.api = new apigateway.RestApi(this, "SlackWebhookApi", {
      restApiName: prefix ? `${prefix}-slack-webhook-api` : "slack-webhook-api",
      description: "API Gateway for Slack webhook interactions",
      deployOptions: {
        stageName: "prod",
        throttlingRateLimit: 100,
        throttlingBurstLimit: 200,
      },
      endpointConfiguration: {
        types: [apigateway.EndpointType.REGIONAL],
      },
    });

    // Lambda 統合の作成
    const lambdaIntegration = new apigateway.LambdaIntegration(
      this.webhookFunction,
      {
        proxy: true,
      }
    );

    // POST /webhook エンドポイントの作成
    const webhookResource = this.api.root.addResource("webhook");
    webhookResource.addMethod("POST", lambdaIntegration);

    // Webhook URL を設定
    this.webhookUrl = `${this.api.url}webhook`;

    // 検証環境対応: 削除ポリシーを設定
    // Requirements: 6.2
    this.messageTable.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);
  }
}
