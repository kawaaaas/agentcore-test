import * as bedrockagentcore from "aws-cdk-lib/aws-bedrockagentcore";
import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";

/**
 * AgentIdentityConstruct のプロパティ
 */
export interface AgentIdentityConstructProps {
  /**
   * WorkloadIdentity 名（必須）
   * パターン: [A-Za-z0-9_.-]+
   * 長さ: 3-255
   */
  readonly name: string;

  /**
   * OAuth2 リターン URL のリスト（オプション）
   * 各 URL の長さ: 1-2048
   */
  readonly allowedResourceOauth2ReturnUrls?: string[];

  /**
   * タグ（オプション）
   */
  readonly tags?: { [key: string]: string };
}

/**
 * AgentCore WorkloadIdentity を管理する Construct
 * CfnWorkloadIdentity（L1）を使用して AWS::BedrockAgentCore::WorkloadIdentity を作成
 *
 * Requirements: 4.1, 4.2, 4.3
 */
export class AgentIdentityConstruct extends Construct {
  /**
   * WorkloadIdentity リソース（L1 コンストラクト）
   */
  public readonly workloadIdentity: bedrockagentcore.CfnWorkloadIdentity;

  /**
   * WorkloadIdentity ARN
   */
  public readonly workloadIdentityArn: string;

  /**
   * WorkloadIdentity 名
   */
  public readonly workloadIdentityName: string;

  constructor(
    scope: Construct,
    id: string,
    props: AgentIdentityConstructProps
  ) {
    super(scope, id);

    // Name のバリデーション
    // パターン: [A-Za-z0-9_.-]+、長さ: 3-255
    const namePattern = /^[A-Za-z0-9_.-]+$/;
    if (!namePattern.test(props.name)) {
      throw new Error(
        `Name must match pattern [A-Za-z0-9_.-]+, got ${props.name}`
      );
    }
    if (props.name.length < 3 || props.name.length > 255) {
      throw new Error(
        `Name length must be between 3 and 255, got ${props.name.length}`
      );
    }

    // AllowedResourceOauth2ReturnUrls のバリデーション
    // Requirements: 4.3
    if (props.allowedResourceOauth2ReturnUrls) {
      for (const url of props.allowedResourceOauth2ReturnUrls) {
        if (url.length < 1 || url.length > 2048) {
          throw new Error(
            `OAuth2 return URL length must be between 1 and 2048, got ${url.length}`
          );
        }
      }
    }

    // CfnWorkloadIdentity（L1）を使用して AWS::BedrockAgentCore::WorkloadIdentity を作成
    // Requirements: 4.1, 4.2
    this.workloadIdentity = new bedrockagentcore.CfnWorkloadIdentity(
      this,
      "WorkloadIdentity",
      {
        name: props.name,
        allowedResourceOauth2ReturnUrls: props.allowedResourceOauth2ReturnUrls,
        tags: props.tags
          ? Object.entries(props.tags).map(([key, value]) => ({
              key,
              value,
            }))
          : undefined,
      }
    );

    // 検証環境対応: 削除ポリシーを設定
    // Requirements: 6.2
    this.workloadIdentity.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    // 出力値を設定
    this.workloadIdentityArn = this.workloadIdentity.attrWorkloadIdentityArn;
    this.workloadIdentityName = props.name;
  }
}
