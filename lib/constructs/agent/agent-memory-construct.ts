import * as bedrockagentcore from "aws-cdk-lib/aws-bedrockagentcore";
import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";

/**
 * Semantic Memory Strategy の設定
 */
export interface SemanticMemoryStrategyConfig {
  /**
   * 戦略名（必須）
   * パターン: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$
   */
  readonly name: string;
  /**
   * 戦略の説明（オプション）
   */
  readonly description?: string;
  /**
   * 名前空間（オプション）
   */
  readonly namespaces?: string[];
}

/**
 * Summary Memory Strategy の設定
 */
export interface SummaryMemoryStrategyConfig {
  /**
   * 戦略名（必須）
   */
  readonly name: string;
  /**
   * 戦略の説明（オプション）
   */
  readonly description?: string;
  /**
   * 名前空間（オプション）
   */
  readonly namespaces?: string[];
}

/**
 * User Preference Memory Strategy の設定
 */
export interface UserPreferenceMemoryStrategyConfig {
  /**
   * 戦略名（必須）
   */
  readonly name: string;
  /**
   * 戦略の説明（オプション）
   */
  readonly description?: string;
  /**
   * 名前空間（オプション）
   */
  readonly namespaces?: string[];
}

/**
 * Custom Memory Strategy の設定
 */
export interface CustomMemoryStrategyConfig {
  /**
   * 戦略名（必須）
   */
  readonly name: string;
  /**
   * 戦略の説明（オプション）
   */
  readonly description?: string;
  /**
   * 名前空間（オプション）
   */
  readonly namespaces?: string[];
}

/**
 * Memory Strategy の設定（Union 型）
 */
export interface MemoryStrategyConfig {
  /**
   * Semantic Memory Strategy（オプション）
   */
  readonly semanticMemoryStrategy?: SemanticMemoryStrategyConfig;
  /**
   * Summary Memory Strategy（オプション）
   */
  readonly summaryMemoryStrategy?: SummaryMemoryStrategyConfig;
  /**
   * User Preference Memory Strategy（オプション）
   */
  readonly userPreferenceMemoryStrategy?: UserPreferenceMemoryStrategyConfig;
  /**
   * Custom Memory Strategy（オプション）
   */
  readonly customMemoryStrategy?: CustomMemoryStrategyConfig;
}

/**
 * AgentMemoryConstruct のプロパティ
 */
export interface AgentMemoryConstructProps {
  /**
   * Memory 名（必須）
   * パターン: ^[a-zA-Z][a-zA-Z0-9_]{0,47}$
   */
  readonly name: string;

  /**
   * イベント有効期限（日数）（必須）
   * 範囲: 7-365
   * @default 90
   */
  readonly eventExpiryDuration?: number;

  /**
   * Memory の説明（オプション）
   */
  readonly description?: string;

  /**
   * 暗号化キーの ARN（オプション）
   * パターン: ^arn:aws:[a-z0-9-\.]{0,63}:[a-z0-9-\.]{0,63}:[a-z0-9-\.]{0,63}:[^/].{0,1023}$
   */
  readonly encryptionKeyArn?: string;

  /**
   * Memory 実行ロールの ARN（オプション）
   */
  readonly memoryExecutionRoleArn?: string;

  /**
   * Memory 戦略（オプション）
   */
  readonly memoryStrategies?: MemoryStrategyConfig[];

  /**
   * タグ（オプション）
   */
  readonly tags?: { [key: string]: string };
}

/**
 * AgentCore Memory を管理する Construct
 * CfnMemory（L1）を使用して AWS::BedrockAgentCore::Memory を作成
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4
 */
export class AgentMemoryConstruct extends Construct {
  /**
   * Memory リソース（L1 コンストラクト）
   */
  public readonly memory: bedrockagentcore.CfnMemory;

  /**
   * Memory ARN
   */
  public readonly memoryArn: string;

  /**
   * Memory ID
   */
  public readonly memoryId: string;

  constructor(scope: Construct, id: string, props: AgentMemoryConstructProps) {
    super(scope, id);

    // EventExpiryDuration のバリデーション（7-365）
    // Requirements: 3.2
    const eventExpiryDuration = props.eventExpiryDuration ?? 90;
    if (eventExpiryDuration < 7 || eventExpiryDuration > 365) {
      throw new Error(
        `EventExpiryDuration must be between 7 and 365, got ${eventExpiryDuration}`
      );
    }

    // Name のバリデーション
    const namePattern = /^[a-zA-Z][a-zA-Z0-9_]{0,47}$/;
    if (!namePattern.test(props.name)) {
      throw new Error(
        `Name must match pattern ^[a-zA-Z][a-zA-Z0-9_]{0,47}$, got ${props.name}`
      );
    }

    // MemoryStrategies の変換
    // Requirements: 3.3
    const memoryStrategies = props.memoryStrategies?.map(
      (strategy): bedrockagentcore.CfnMemory.MemoryStrategyProperty => {
        return {
          semanticMemoryStrategy: strategy.semanticMemoryStrategy
            ? {
                name: strategy.semanticMemoryStrategy.name,
                description: strategy.semanticMemoryStrategy.description,
                namespaces: strategy.semanticMemoryStrategy.namespaces,
              }
            : undefined,
          summaryMemoryStrategy: strategy.summaryMemoryStrategy
            ? {
                name: strategy.summaryMemoryStrategy.name,
                description: strategy.summaryMemoryStrategy.description,
                namespaces: strategy.summaryMemoryStrategy.namespaces,
              }
            : undefined,
          userPreferenceMemoryStrategy: strategy.userPreferenceMemoryStrategy
            ? {
                name: strategy.userPreferenceMemoryStrategy.name,
                description: strategy.userPreferenceMemoryStrategy.description,
                namespaces: strategy.userPreferenceMemoryStrategy.namespaces,
              }
            : undefined,
          customMemoryStrategy: strategy.customMemoryStrategy
            ? {
                name: strategy.customMemoryStrategy.name,
                description: strategy.customMemoryStrategy.description,
                namespaces: strategy.customMemoryStrategy.namespaces,
              }
            : undefined,
        };
      }
    );

    // CfnMemory（L1）を使用して AWS::BedrockAgentCore::Memory を作成
    // Requirements: 3.1
    this.memory = new bedrockagentcore.CfnMemory(this, "Memory", {
      name: props.name,
      eventExpiryDuration: eventExpiryDuration,
      description: props.description,
      encryptionKeyArn: props.encryptionKeyArn,
      memoryExecutionRoleArn: props.memoryExecutionRoleArn,
      memoryStrategies: memoryStrategies,
      tags: props.tags,
    });

    // 検証環境対応: 削除ポリシーを設定
    // Requirements: 6.2
    this.memory.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    // 出力値を設定
    this.memoryArn = this.memory.attrMemoryArn;
    this.memoryId = this.memory.attrMemoryId;
  }
}
