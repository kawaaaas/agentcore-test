import * as bedrockagentcore from "aws-cdk-lib/aws-bedrockagentcore";
import * as iam from "aws-cdk-lib/aws-iam";
import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";

/**
 * Gateway の認証タイプ
 */
export type GatewayAuthorizerType = "CUSTOM_JWT" | "AWS_IAM" | "NONE";

/**
 * Gateway のプロトコルタイプ
 */
export type GatewayProtocolType = "MCP";

/**
 * 認証設定（CUSTOM_JWT 用）
 */
export interface CustomJwtAuthorizerConfig {
  /**
   * Discovery URL（必須）
   */
  readonly discoveryUrl: string;
  /**
   * 許可されたオーディエンス（オプション）
   */
  readonly allowedAudience?: string[];
  /**
   * 許可されたクライアント（オプション）
   */
  readonly allowedClients?: string[];
}

/**
 * AgentGatewayConstruct のプロパティ
 */
export interface AgentGatewayConstructProps {
  /**
   * Gateway 名（必須）
   * パターン: ^([0-9a-zA-Z][-]?){1,100}$
   */
  readonly name: string;

  /**
   * 認証タイプ（必須）
   * CUSTOM_JWT | AWS_IAM | NONE
   */
  readonly authorizerType: GatewayAuthorizerType;

  /**
   * プロトコルタイプ（必須）
   * 現在は MCP のみサポート
   * @default "MCP"
   */
  readonly protocolType?: GatewayProtocolType;

  /**
   * Gateway の説明（オプション）
   * 長さ: 1-200
   */
  readonly description?: string;

  /**
   * 例外レベル（オプション）
   * DEBUG のみサポート
   */
  readonly exceptionLevel?: "DEBUG";

  /**
   * KMS キー ARN（オプション）
   */
  readonly kmsKeyArn?: string;

  /**
   * CUSTOM_JWT 認証設定（オプション）
   * authorizerType が CUSTOM_JWT の場合に使用
   */
  readonly customJwtAuthorizerConfig?: CustomJwtAuthorizerConfig;

  /**
   * タグ（オプション）
   */
  readonly tags?: { [key: string]: string };
}

/**
 * MCP サーバーターゲット設定
 */
export interface McpServerTargetConfig {
  /**
   * MCP サーバーエンドポイント URL
   */
  readonly endpoint: string;
}

/**
 * Lambda ターゲット設定
 */
export interface McpLambdaTargetConfig {
  /**
   * Lambda 関数 ARN
   */
  readonly lambdaArn: string;
  /**
   * ツールスキーマ S3 設定（必須）
   */
  readonly toolSchemaS3: {
    readonly uri?: string;
    readonly bucketOwnerAccountId?: string;
  };
}

/**
 * OpenAPI スキーマターゲット設定
 */
export interface OpenApiSchemaTargetConfig {
  /**
   * インラインペイロード（JSON/YAML 文字列）
   */
  readonly inlinePayload?: string;
  /**
   * S3 設定
   */
  readonly s3?: {
    readonly uri?: string;
    readonly bucketOwnerAccountId?: string;
  };
}

/**
 * ターゲット設定（Union 型）
 */
export interface GatewayTargetConfig {
  /**
   * MCP サーバーターゲット（オプション）
   */
  readonly mcpServer?: McpServerTargetConfig;
  /**
   * Lambda ターゲット（オプション）
   */
  readonly lambda?: McpLambdaTargetConfig;
  /**
   * OpenAPI スキーマターゲット（オプション）
   */
  readonly openApiSchema?: OpenApiSchemaTargetConfig;
}

/**
 * 認証プロバイダータイプ
 */
export type CredentialProviderType = "GATEWAY_IAM_ROLE" | "OAUTH" | "API_KEY";

/**
 * OAuth 認証プロバイダー設定
 */
export interface OAuthCredentialProviderConfig {
  /**
   * プロバイダー ARN（必須）
   */
  readonly providerArn: string;
  /**
   * スコープ（必須）
   */
  readonly scopes: string[];
  /**
   * カスタムパラメータ（オプション）
   */
  readonly customParameters?: { [key: string]: string };
}

/**
 * API キー認証プロバイダー設定
 */
export interface ApiKeyCredentialProviderConfig {
  /**
   * プロバイダー ARN（必須）
   */
  readonly providerArn: string;
  /**
   * 認証プレフィックス（オプション）
   */
  readonly credentialPrefix?: string;
  /**
   * 認証場所（オプション）
   */
  readonly credentialLocation?: string;
  /**
   * 認証パラメータ名（オプション）
   */
  readonly credentialParameterName?: string;
}

/**
 * 認証プロバイダー設定
 */
export interface CredentialProviderConfig {
  /**
   * 認証プロバイダータイプ
   */
  readonly credentialProviderType: CredentialProviderType;
  /**
   * OAuth 認証プロバイダー（オプション）
   */
  readonly oauthCredentialProvider?: OAuthCredentialProviderConfig;
  /**
   * API キー認証プロバイダー（オプション）
   */
  readonly apiKeyCredentialProvider?: ApiKeyCredentialProviderConfig;
}

/**
 * GatewayTarget 追加用のプロパティ
 */
export interface AddGatewayTargetProps {
  /**
   * ターゲット名（必須）
   * パターン: ^([0-9a-zA-Z][-]?){1,100}$
   */
  readonly name: string;

  /**
   * ターゲット設定（必須）
   */
  readonly targetConfiguration: GatewayTargetConfig;

  /**
   * 認証プロバイダー設定（必須）
   */
  readonly credentialProviderConfigurations: CredentialProviderConfig[];

  /**
   * ターゲットの説明（オプション）
   * 長さ: 1-200
   */
  readonly description?: string;
}

/**
 * AgentCore Gateway を管理する Construct
 * CfnGateway（L1）を使用して AWS::BedrockAgentCore::Gateway を作成
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 */
export class AgentGatewayConstruct extends Construct {
  /**
   * Gateway リソース（L1 コンストラクト）
   */
  public readonly gateway: bedrockagentcore.CfnGateway;

  /**
   * Gateway ARN
   */
  public readonly gatewayArn: string;

  /**
   * Gateway ID
   */
  public readonly gatewayId: string;

  /**
   * Gateway URL
   */
  public readonly gatewayUrl: string;

  /**
   * Gateway 用 IAM ロール
   */
  public readonly role: iam.Role;

  /**
   * 追加された GatewayTarget のリスト
   */
  private readonly targets: bedrockagentcore.CfnGatewayTarget[] = [];

  constructor(scope: Construct, id: string, props: AgentGatewayConstructProps) {
    super(scope, id);

    // Name のバリデーション
    // パターン: ^([0-9a-zA-Z][-]?){1,100}$
    const namePattern = /^([0-9a-zA-Z][-]?){1,100}$/;
    if (!namePattern.test(props.name)) {
      throw new Error(
        `Name must match pattern ^([0-9a-zA-Z][-]?){1,100}$, got ${props.name}`
      );
    }

    // Description のバリデーション
    if (props.description) {
      if (props.description.length < 1 || props.description.length > 200) {
        throw new Error(
          `Description length must be between 1 and 200, got ${props.description.length}`
        );
      }
    }

    // Gateway 用 IAM ロールを作成
    // Requirements: 6.3
    this.role = new iam.Role(this, "GatewayRole", {
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
      description: `IAM role for AgentCore Gateway: ${props.name}`,
    });

    // AuthorizerConfiguration の構築
    let authorizerConfiguration:
      | bedrockagentcore.CfnGateway.AuthorizerConfigurationProperty
      | undefined;
    if (
      props.authorizerType === "CUSTOM_JWT" &&
      props.customJwtAuthorizerConfig
    ) {
      authorizerConfiguration = {
        customJwtAuthorizer: {
          discoveryUrl: props.customJwtAuthorizerConfig.discoveryUrl,
          allowedAudience: props.customJwtAuthorizerConfig.allowedAudience,
          allowedClients: props.customJwtAuthorizerConfig.allowedClients,
        },
      };
    }

    // CfnGateway（L1）を使用して AWS::BedrockAgentCore::Gateway を作成
    // Requirements: 2.1, 2.2, 2.3
    this.gateway = new bedrockagentcore.CfnGateway(this, "Gateway", {
      name: props.name,
      authorizerType: props.authorizerType,
      protocolType: props.protocolType ?? "MCP",
      roleArn: this.role.roleArn,
      description: props.description,
      exceptionLevel: props.exceptionLevel,
      kmsKeyArn: props.kmsKeyArn,
      authorizerConfiguration: authorizerConfiguration,
      tags: props.tags,
    });

    // 検証環境対応: 削除ポリシーを設定
    // Requirements: 6.2
    this.gateway.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    // 出力値を設定
    this.gatewayArn = this.gateway.attrGatewayArn;
    this.gatewayId = this.gateway.attrGatewayIdentifier;
    this.gatewayUrl = this.gateway.attrGatewayUrl;
  }

  /**
   * GatewayTarget を追加する
   * CfnGatewayTarget（L1）を使用して AWS::BedrockAgentCore::GatewayTarget を作成
   *
   * Requirements: 2.4, 2.5
   *
   * @param id コンストラクト ID
   * @param props GatewayTarget のプロパティ
   * @returns 作成された CfnGatewayTarget
   */
  public addTarget(
    id: string,
    props: AddGatewayTargetProps
  ): bedrockagentcore.CfnGatewayTarget {
    // Name のバリデーション
    const namePattern = /^([0-9a-zA-Z][-]?){1,100}$/;
    if (!namePattern.test(props.name)) {
      throw new Error(
        `Target name must match pattern ^([0-9a-zA-Z][-]?){1,100}$, got ${props.name}`
      );
    }

    // Description のバリデーション
    if (props.description) {
      if (props.description.length < 1 || props.description.length > 200) {
        throw new Error(
          `Target description length must be between 1 and 200, got ${props.description.length}`
        );
      }
    }

    // CredentialProviderConfigurations のバリデーション
    if (
      props.credentialProviderConfigurations.length < 1 ||
      props.credentialProviderConfigurations.length > 1
    ) {
      throw new Error(
        `CredentialProviderConfigurations must have exactly 1 item, got ${props.credentialProviderConfigurations.length}`
      );
    }

    // TargetConfiguration の構築
    // Requirements: 2.4
    const targetConfiguration = this.buildTargetConfiguration(
      props.targetConfiguration
    );

    // CredentialProviderConfigurations の構築
    // Requirements: 2.5
    const credentialProviderConfigurations =
      props.credentialProviderConfigurations.map((config) =>
        this.buildCredentialProviderConfiguration(config)
      );

    // CfnGatewayTarget を作成
    const target = new bedrockagentcore.CfnGatewayTarget(this, id, {
      gatewayIdentifier: this.gatewayId,
      name: props.name,
      targetConfiguration: targetConfiguration,
      credentialProviderConfigurations: credentialProviderConfigurations,
      description: props.description,
    });

    // 検証環境対応: 削除ポリシーを設定
    target.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    // Gateway への依存関係を追加
    target.addDependency(this.gateway);

    this.targets.push(target);
    return target;
  }

  /**
   * TargetConfiguration を構築する
   */
  private buildTargetConfiguration(
    config: GatewayTargetConfig
  ): bedrockagentcore.CfnGatewayTarget.TargetConfigurationProperty {
    // MCP ターゲット設定を構築
    const mcpConfig: bedrockagentcore.CfnGatewayTarget.McpTargetConfigurationProperty =
      {
        mcpServer: config.mcpServer
          ? {
              endpoint: config.mcpServer.endpoint,
            }
          : undefined,
        lambda: config.lambda
          ? {
              lambdaArn: config.lambda.lambdaArn,
              toolSchema: {
                s3: {
                  uri: config.lambda.toolSchemaS3.uri,
                  bucketOwnerAccountId:
                    config.lambda.toolSchemaS3.bucketOwnerAccountId,
                },
              },
            }
          : undefined,
        openApiSchema: config.openApiSchema
          ? {
              inlinePayload: config.openApiSchema.inlinePayload,
              s3: config.openApiSchema.s3
                ? {
                    uri: config.openApiSchema.s3.uri,
                    bucketOwnerAccountId:
                      config.openApiSchema.s3.bucketOwnerAccountId,
                  }
                : undefined,
            }
          : undefined,
      };

    return {
      mcp: mcpConfig,
    };
  }

  /**
   * CredentialProviderConfiguration を構築する
   */
  private buildCredentialProviderConfiguration(
    config: CredentialProviderConfig
  ): bedrockagentcore.CfnGatewayTarget.CredentialProviderConfigurationProperty {
    // CredentialProvider を構築
    const credentialProvider:
      | bedrockagentcore.CfnGatewayTarget.CredentialProviderProperty
      | undefined =
      config.oauthCredentialProvider || config.apiKeyCredentialProvider
        ? {
            oauthCredentialProvider: config.oauthCredentialProvider
              ? {
                  providerArn: config.oauthCredentialProvider.providerArn,
                  scopes: config.oauthCredentialProvider.scopes,
                  customParameters:
                    config.oauthCredentialProvider.customParameters,
                }
              : undefined,
            apiKeyCredentialProvider: config.apiKeyCredentialProvider
              ? {
                  providerArn: config.apiKeyCredentialProvider.providerArn,
                  credentialPrefix:
                    config.apiKeyCredentialProvider.credentialPrefix,
                  credentialLocation:
                    config.apiKeyCredentialProvider.credentialLocation,
                  credentialParameterName:
                    config.apiKeyCredentialProvider.credentialParameterName,
                }
              : undefined,
          }
        : undefined;

    return {
      credentialProviderType: config.credentialProviderType,
      credentialProvider: credentialProvider,
    };
  }

  /**
   * 追加された GatewayTarget のリストを取得する
   */
  public getTargets(): bedrockagentcore.CfnGatewayTarget[] {
    return [...this.targets];
  }
}
