import * as bedrockagentcore from "aws-cdk-lib/aws-bedrockagentcore";
import * as iam from "aws-cdk-lib/aws-iam";
import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";

/**
 * ネットワークモード
 */
export type NetworkMode = "PUBLIC" | "VPC";

/**
 * プロトコル設定
 */
export type ProtocolConfiguration = "MCP" | "HTTP" | "A2A";

/**
 * Python ランタイムバージョン
 */
export type PythonRuntime =
  | "PYTHON_3_10"
  | "PYTHON_3_11"
  | "PYTHON_3_12"
  | "PYTHON_3_13";

/**
 * S3 ロケーション設定
 */
export interface S3LocationConfig {
  /**
   * S3 バケット名（必須）
   * パターン: ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$
   */
  readonly bucket: string;
  /**
   * S3 プレフィックス（必須）
   * 長さ: 1-1024
   */
  readonly prefix: string;
  /**
   * S3 バージョン ID（オプション）
   * 長さ: 3-1024
   */
  readonly versionId?: string;
}

/**
 * コード設定（S3 からのコードデプロイ用）
 */
export interface CodeConfig {
  /**
   * S3 ロケーション（必須）
   */
  readonly s3: S3LocationConfig;
  /**
   * エントリポイント（必須）
   * 配列長: 1-2
   */
  readonly entryPoint: string[];
  /**
   * Python ランタイム（必須）
   */
  readonly runtime: PythonRuntime;
}

/**
 * コンテナ設定（ECR からのコンテナデプロイ用）
 */
export interface ContainerConfig {
  /**
   * コンテナ URI（必須）
   * パターン: ^\d{12}\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com/...
   * 長さ: 1-1024
   */
  readonly containerUri: string;
}

/**
 * エージェントランタイムアーティファクト設定
 * CodeConfig または ContainerConfig のいずれかを指定
 */
export interface AgentRuntimeArtifactConfig {
  /**
   * コード設定（オプション）
   * S3 からのコードデプロイ用
   */
  readonly codeConfiguration?: CodeConfig;
  /**
   * コンテナ設定（オプション）
   * ECR からのコンテナデプロイ用
   */
  readonly containerConfiguration?: ContainerConfig;
}

/**
 * VPC 設定
 */
export interface VpcConfig {
  /**
   * セキュリティグループ ID のリスト（必須）
   * 配列長: 1-16
   */
  readonly securityGroups: string[];
  /**
   * サブネット ID のリスト（必須）
   * 配列長: 1-16
   */
  readonly subnets: string[];
}

/**
 * ネットワーク設定
 */
export interface NetworkConfig {
  /**
   * ネットワークモード（必須）
   * PUBLIC または VPC
   */
  readonly networkMode: NetworkMode;
  /**
   * VPC 設定（オプション）
   * networkMode が VPC の場合に必須
   */
  readonly vpcConfig?: VpcConfig;
}

/**
 * ライフサイクル設定
 */
export interface LifecycleConfig {
  /**
   * アイドルランタイムセッションタイムアウト（秒）（オプション）
   * 範囲: 60-28800
   */
  readonly idleRuntimeSessionTimeout?: number;
  /**
   * 最大ライフタイム（秒）（オプション）
   * 範囲: 60-28800
   */
  readonly maxLifetime?: number;
}

/**
 * AgentRuntimeConstruct のプロパティ
 */
export interface AgentRuntimeConstructProps {
  /**
   * Runtime 名（必須）
   * パターン: [a-zA-Z][a-zA-Z0-9_]{0,47}
   */
  readonly name: string;

  /**
   * エージェントランタイムアーティファクト（必須）
   * CodeConfig または ContainerConfig のいずれかを指定
   */
  readonly agentRuntimeArtifact: AgentRuntimeArtifactConfig;

  /**
   * ネットワーク設定（必須）
   */
  readonly networkConfiguration: NetworkConfig;

  /**
   * プロトコル設定（オプション）
   * MCP | HTTP | A2A
   * @default "HTTP"
   */
  readonly protocolConfiguration?: ProtocolConfiguration;

  /**
   * ライフサイクル設定（オプション）
   */
  readonly lifecycleConfiguration?: LifecycleConfig;

  /**
   * Runtime の説明（オプション）
   * 長さ: 1-1200
   */
  readonly description?: string;

  /**
   * 環境変数（オプション）
   */
  readonly environmentVariables?: { [key: string]: string };

  /**
   * タグ（オプション）
   */
  readonly tags?: { [key: string]: string };
}

/**
 * RuntimeEndpoint 追加用のプロパティ
 */
export interface AddRuntimeEndpointProps {
  /**
   * エンドポイント名（必須）
   * パターン: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$
   * 長さ: 1-48
   */
  readonly name: string;

  /**
   * エージェントランタイムバージョン（オプション）
   * パターン: ^([1-9][0-9]{0,4})$
   */
  readonly agentRuntimeVersion?: string;

  /**
   * エンドポイントの説明（オプション）
   * 長さ: 1-256
   */
  readonly description?: string;

  /**
   * タグ（オプション）
   */
  readonly tags?: { [key: string]: string };
}

/**
 * AgentCore Runtime を管理する Construct
 * CfnRuntime（L1）を使用して AWS::BedrockAgentCore::Runtime を作成
 *
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.3
 */
export class AgentRuntimeConstruct extends Construct {
  /**
   * Runtime リソース（L1 コンストラクト）
   */
  public readonly runtime: bedrockagentcore.CfnRuntime;

  /**
   * Runtime ARN
   */
  public readonly runtimeArn: string;

  /**
   * Runtime ID
   */
  public readonly runtimeId: string;

  /**
   * Runtime バージョン
   */
  public readonly runtimeVersion: string;

  /**
   * Runtime 用 IAM ロール
   */
  public readonly role: iam.Role;

  /**
   * 追加された RuntimeEndpoint のリスト
   */
  private readonly endpoints: bedrockagentcore.CfnRuntimeEndpoint[] = [];

  constructor(scope: Construct, id: string, props: AgentRuntimeConstructProps) {
    super(scope, id);

    // Name のバリデーション
    // パターン: [a-zA-Z][a-zA-Z0-9_]{0,47}
    const namePattern = /^[a-zA-Z][a-zA-Z0-9_]{0,47}$/;
    if (!namePattern.test(props.name)) {
      throw new Error(
        `Name must match pattern [a-zA-Z][a-zA-Z0-9_]{0,47}, got ${props.name}`
      );
    }

    // Description のバリデーション
    if (props.description) {
      if (props.description.length < 1 || props.description.length > 1200) {
        throw new Error(
          `Description length must be between 1 and 1200, got ${props.description.length}`
        );
      }
    }

    // AgentRuntimeArtifact のバリデーション
    // CodeConfig または ContainerConfig のいずれかが必須
    if (
      !props.agentRuntimeArtifact.codeConfiguration &&
      !props.agentRuntimeArtifact.containerConfiguration
    ) {
      throw new Error(
        "AgentRuntimeArtifact must have either codeConfiguration or containerConfiguration"
      );
    }
    if (
      props.agentRuntimeArtifact.codeConfiguration &&
      props.agentRuntimeArtifact.containerConfiguration
    ) {
      throw new Error(
        "AgentRuntimeArtifact cannot have both codeConfiguration and containerConfiguration"
      );
    }

    // LifecycleConfiguration のバリデーション
    // Requirements: 1.4
    if (props.lifecycleConfiguration) {
      if (
        props.lifecycleConfiguration.idleRuntimeSessionTimeout !== undefined
      ) {
        const timeout = props.lifecycleConfiguration.idleRuntimeSessionTimeout;
        if (timeout < 60 || timeout > 28800) {
          throw new Error(
            `IdleRuntimeSessionTimeout must be between 60 and 28800, got ${timeout}`
          );
        }
      }
      if (props.lifecycleConfiguration.maxLifetime !== undefined) {
        const maxLifetime = props.lifecycleConfiguration.maxLifetime;
        if (maxLifetime < 60 || maxLifetime > 28800) {
          throw new Error(
            `MaxLifetime must be between 60 and 28800, got ${maxLifetime}`
          );
        }
      }
    }

    // NetworkConfiguration のバリデーション
    // Requirements: 1.3
    if (
      props.networkConfiguration.networkMode === "VPC" &&
      !props.networkConfiguration.vpcConfig
    ) {
      throw new Error("VpcConfig is required when networkMode is VPC");
    }

    // Runtime 用 IAM ロールを作成
    // Requirements: 6.3
    this.role = new iam.Role(this, "RuntimeRole", {
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
      description: `IAM role for AgentCore Runtime: ${props.name}`,
    });

    // Bedrock モデル呼び出し権限を付与
    // Requirements: 6.3
    this.role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // CloudWatch Logs 権限を付与
    // Requirements: 6.3
    this.role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        resources: ["*"],
      })
    );

    // AgentRuntimeArtifact の構築
    // Requirements: 1.2
    const agentRuntimeArtifact = this.buildAgentRuntimeArtifact(
      props.agentRuntimeArtifact
    );

    // NetworkConfiguration の構築
    // Requirements: 1.3
    const networkConfiguration = this.buildNetworkConfiguration(
      props.networkConfiguration
    );

    // LifecycleConfiguration の構築
    // Requirements: 1.4
    const lifecycleConfiguration = props.lifecycleConfiguration
      ? {
          idleRuntimeSessionTimeout:
            props.lifecycleConfiguration.idleRuntimeSessionTimeout,
          maxLifetime: props.lifecycleConfiguration.maxLifetime,
        }
      : undefined;

    // CfnRuntime（L1）を使用して AWS::BedrockAgentCore::Runtime を作成
    // Requirements: 1.1
    this.runtime = new bedrockagentcore.CfnRuntime(this, "Runtime", {
      agentRuntimeName: props.name,
      agentRuntimeArtifact: agentRuntimeArtifact,
      networkConfiguration: networkConfiguration,
      roleArn: this.role.roleArn,
      protocolConfiguration: props.protocolConfiguration,
      lifecycleConfiguration: lifecycleConfiguration,
      description: props.description,
      environmentVariables: props.environmentVariables,
      tags: props.tags,
    });

    // 検証環境対応: 削除ポリシーを設定
    // Requirements: 6.2
    this.runtime.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    // 出力値を設定
    this.runtimeArn = this.runtime.attrAgentRuntimeArn;
    this.runtimeId = this.runtime.attrAgentRuntimeId;
    this.runtimeVersion = this.runtime.attrAgentRuntimeVersion;
  }

  /**
   * RuntimeEndpoint を追加する
   * CfnRuntimeEndpoint（L1）を使用して AWS::BedrockAgentCore::RuntimeEndpoint を作成
   *
   * Requirements: 1.5
   *
   * @param id コンストラクト ID
   * @param props RuntimeEndpoint のプロパティ
   * @returns 作成された CfnRuntimeEndpoint
   */
  public addEndpoint(
    id: string,
    props: AddRuntimeEndpointProps
  ): bedrockagentcore.CfnRuntimeEndpoint {
    // Name のバリデーション
    // パターン: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$
    const namePattern = /^[a-zA-Z][a-zA-Z0-9_]{0,47}$/;
    if (!namePattern.test(props.name)) {
      throw new Error(
        `Endpoint name must match pattern ^[a-zA-Z][a-zA-Z0-9_]{0,47}$, got ${props.name}`
      );
    }
    if (props.name.length < 1 || props.name.length > 48) {
      throw new Error(
        `Endpoint name length must be between 1 and 48, got ${props.name.length}`
      );
    }

    // Description のバリデーション
    if (props.description) {
      if (props.description.length < 1 || props.description.length > 256) {
        throw new Error(
          `Endpoint description length must be between 1 and 256, got ${props.description.length}`
        );
      }
    }

    // AgentRuntimeVersion のバリデーション
    if (props.agentRuntimeVersion) {
      const versionPattern = /^([1-9][0-9]{0,4})$/;
      if (!versionPattern.test(props.agentRuntimeVersion)) {
        throw new Error(
          `AgentRuntimeVersion must match pattern ^([1-9][0-9]{0,4})$, got ${props.agentRuntimeVersion}`
        );
      }
    }

    // CfnRuntimeEndpoint を作成
    // Requirements: 1.5
    const endpoint = new bedrockagentcore.CfnRuntimeEndpoint(this, id, {
      agentRuntimeId: this.runtimeId,
      name: props.name,
      agentRuntimeVersion: props.agentRuntimeVersion,
      description: props.description,
      tags: props.tags,
    });

    // 検証環境対応: 削除ポリシーを設定
    endpoint.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    // Runtime への依存関係を追加
    endpoint.addDependency(this.runtime);

    this.endpoints.push(endpoint);
    return endpoint;
  }

  /**
   * AgentRuntimeArtifact を構築する
   */
  private buildAgentRuntimeArtifact(
    config: AgentRuntimeArtifactConfig
  ): bedrockagentcore.CfnRuntime.AgentRuntimeArtifactProperty {
    if (config.codeConfiguration) {
      return {
        codeConfiguration: {
          code: {
            s3: {
              bucket: config.codeConfiguration.s3.bucket,
              prefix: config.codeConfiguration.s3.prefix,
              versionId: config.codeConfiguration.s3.versionId,
            },
          },
          entryPoint: config.codeConfiguration.entryPoint,
          runtime: config.codeConfiguration.runtime,
        },
      };
    }

    if (config.containerConfiguration) {
      return {
        containerConfiguration: {
          containerUri: config.containerConfiguration.containerUri,
        },
      };
    }

    // バリデーションで既にチェック済みなので、ここには到達しない
    throw new Error(
      "AgentRuntimeArtifact must have either codeConfiguration or containerConfiguration"
    );
  }

  /**
   * NetworkConfiguration を構築する
   */
  private buildNetworkConfiguration(
    config: NetworkConfig
  ): bedrockagentcore.CfnRuntime.NetworkConfigurationProperty {
    return {
      networkMode: config.networkMode,
      networkModeConfig: config.vpcConfig
        ? {
            securityGroups: config.vpcConfig.securityGroups,
            subnets: config.vpcConfig.subnets,
          }
        : undefined,
    };
  }

  /**
   * 追加された RuntimeEndpoint のリストを取得する
   */
  public getEndpoints(): bedrockagentcore.CfnRuntimeEndpoint[] {
    return [...this.endpoints];
  }
}
