import * as events from "aws-cdk-lib/aws-events";
import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";
import { AgentGatewayConstruct } from "../constructs/agent/agent-gateway-construct";
import { AgentIdentityConstruct } from "../constructs/agent/agent-identity-construct";
import { AgentMemoryConstruct } from "../constructs/agent/agent-memory-construct";
import { AgentRuntimeConstruct } from "../constructs/agent/agent-runtime-construct";
import { StorageConstruct } from "../constructs/storage-construct";

/**
 * MainStack のプロパティ
 */
export interface MainStackProps extends cdk.StackProps {
  /**
   * エージェントコードの S3 バケット名（必須）
   */
  readonly agentCodeBucket: string;
  /**
   * エージェントコードの S3 プレフィックス（必須）
   */
  readonly agentCodePrefix: string;
}

/**
 * メインスタック
 * すべての Construct を組み合わせるエントリーポイント
 * Requirements: 5.1, 6.1, 6.2
 */
export class MainStack extends cdk.Stack {
  /**
   * ストレージリソースを管理する Construct
   */
  public readonly storage: StorageConstruct;

  /**
   * S3 PutObject イベントをトリガーする EventBridge ルール
   */
  public readonly transcriptUploadRule: events.Rule;

  /**
   * AgentCore Memory を管理する Construct
   */
  public readonly agentMemory: AgentMemoryConstruct;

  /**
   * AgentCore WorkloadIdentity を管理する Construct
   */
  public readonly agentIdentity: AgentIdentityConstruct;

  /**
   * AgentCore Gateway を管理する Construct
   */
  public readonly agentGateway: AgentGatewayConstruct;

  /**
   * AgentCore Runtime を管理する Construct
   */
  public readonly agentRuntime: AgentRuntimeConstruct;

  constructor(scope: Construct, id: string, props: MainStackProps) {
    super(scope, id, props);

    // StorageConstruct をインスタンス化
    // Requirements: 5.1, 5.2
    this.storage = new StorageConstruct(this, "Storage");

    // EventBridge ルールを作成
    // Transcript_Bucket への PutObject イベントをトリガー
    // Requirements: 3.1, 3.2, 3.3
    this.transcriptUploadRule = new events.Rule(this, "TranscriptUploadRule", {
      ruleName: "transcript-upload-rule",
      description: "Transcript_Bucket への書き起こしテキストアップロードを検知",
      eventPattern: {
        source: ["aws.s3"],
        detailType: ["Object Created"],
        detail: {
          bucket: {
            name: [this.storage.transcriptBucket.bucketName],
          },
        },
      },
    });

    // AgentMemoryConstruct をインスタンス化
    // Requirements: 3.1, 3.2, 3.3, 3.4, 6.1
    this.agentMemory = new AgentMemoryConstruct(this, "AgentMemory", {
      name: "MeetingAgentMemory",
      eventExpiryDuration: 90, // デフォルト 90 日
      description: "議事録生成エージェント用の Memory（STM/LTM）",
      memoryStrategies: [
        {
          // セマンティックメモリ: 過去の議事録や修正パターンを保存
          semanticMemoryStrategy: {
            name: "meeting_knowledge",
            description: "議事録の知識と修正パターンを保存",
          },
        },
        {
          // ユーザー設定メモリ: ユーザーの好みや文体を記憶
          userPreferenceMemoryStrategy: {
            name: "user_preferences",
            description: "ユーザーの好みや文体の設定を保存",
          },
        },
      ],
    });

    // AgentIdentityConstruct をインスタンス化
    // Requirements: 4.1, 4.2, 4.3, 6.1
    this.agentIdentity = new AgentIdentityConstruct(this, "AgentIdentity", {
      name: "MeetingAgentIdentity",
    });

    // AgentGatewayConstruct をインスタンス化
    // Requirements: 2.1, 2.2, 2.3, 6.1
    this.agentGateway = new AgentGatewayConstruct(this, "AgentGateway", {
      name: "MeetingAgentGateway",
      authorizerType: "AWS_IAM", // IAM 認証を使用
      protocolType: "MCP", // MCP プロトコル
      description: "議事録生成エージェント用の Gateway（MCP 統合）",
    });

    // AgentRuntimeConstruct をインスタンス化
    // Requirements: 1.1, 1.2, 1.3, 1.4, 6.1
    this.agentRuntime = new AgentRuntimeConstruct(this, "AgentRuntime", {
      name: "MeetingAgentRuntime",
      agentRuntimeArtifact: {
        codeConfiguration: {
          s3: {
            bucket: props.agentCodeBucket,
            prefix: props.agentCodePrefix,
          },
          entryPoint: ["meeting_agent.py"],
          runtime: "PYTHON_3_12",
        },
      },
      networkConfiguration: {
        networkMode: "PUBLIC", // パブリックネットワーク
      },
      protocolConfiguration: "HTTP", // HTTP プロトコル
      lifecycleConfiguration: {
        idleRuntimeSessionTimeout: 300, // 5 分
        maxLifetime: 3600, // 1 時間
      },
      description: "議事録生成エージェント用の Runtime",
      environmentVariables: {
        TRANSCRIPT_BUCKET: this.storage.transcriptBucket.bucketName,
        MINUTES_BUCKET: this.storage.minutesBucket.bucketName,
        SESSION_TABLE: this.storage.sessionTable.tableName,
      },
    });

    // RuntimeEndpoint を追加
    // Requirements: 1.5
    this.agentRuntime.addEndpoint("DefaultEndpoint", {
      name: "default_endpoint",
      description: "デフォルトの RuntimeEndpoint",
    });

    // S3 バケットへの読み取り権限を Runtime ロールに付与
    this.storage.transcriptBucket.grantRead(this.agentRuntime.role);
    this.storage.minutesBucket.grantReadWrite(this.agentRuntime.role);

    // DynamoDB テーブルへの読み書き権限を Runtime ロールに付与
    this.storage.sessionTable.grantReadWriteData(this.agentRuntime.role);

    // 出力値を追加
    // Requirements: 6.1, 6.2
    new cdk.CfnOutput(this, "RuntimeArn", {
      value: this.agentRuntime.runtimeArn,
      description: "AgentCore Runtime ARN",
      exportName: `${this.stackName}-RuntimeArn`,
    });

    new cdk.CfnOutput(this, "GatewayArn", {
      value: this.agentGateway.gatewayArn,
      description: "AgentCore Gateway ARN",
      exportName: `${this.stackName}-GatewayArn`,
    });

    new cdk.CfnOutput(this, "MemoryId", {
      value: this.agentMemory.memoryId,
      description: "AgentCore Memory ID",
      exportName: `${this.stackName}-MemoryId`,
    });

    new cdk.CfnOutput(this, "IdentityArn", {
      value: this.agentIdentity.workloadIdentityArn,
      description: "AgentCore WorkloadIdentity ARN",
      exportName: `${this.stackName}-IdentityArn`,
    });
  }
}
