# Requirements Document

## Introduction

AWS AgentCore を活用した AI エージェント実行基盤の構築。Strands Agents SDK と連携し、議事録生成・タスク抽出ワークフローを実行するエージェントの Runtime、Gateway、Memory、WorkloadIdentity 機能を CDK（L1 リソース）で定義する。

## Glossary

- **AgentCore**: AWS が提供するエージェント実行基盤サービス
- **Runtime**: エージェントの非同期実行とセッション管理を担当するコンポーネント（AWS::BedrockAgentCore::Runtime）
- **RuntimeEndpoint**: Runtime のバージョン管理とエンドポイント（AWS::BedrockAgentCore::RuntimeEndpoint）
- **Gateway**: MCP 統合と外部 API 接続を担当するコンポーネント（AWS::BedrockAgentCore::Gateway）
- **GatewayTarget**: Gateway に接続するツールターゲット（AWS::BedrockAgentCore::GatewayTarget）
- **Memory**: 短期記憶（STM）と長期記憶（LTM）を管理するコンポーネント（AWS::BedrockAgentCore::Memory）
- **WorkloadIdentity**: OAuth2 ベースの認証を提供するコンポーネント（AWS::BedrockAgentCore::WorkloadIdentity）
- **Strands_Agents**: Python ベースのエージェント SDK
- **MCP**: Model Context Protocol、ツール接続の標準プロトコル
- **L1_Construct**: CloudFormation リソースを直接ラップする CDK コンストラクト（CfnXxx）

## Requirements

### Requirement 1: エージェント Runtime 設定

**User Story:** As a 開発者, I want to AgentCore Runtime を CDK で定義する, so that エージェントを非同期で実行しセッションを維持できる。

#### Acceptance Criteria

1. WHEN Runtime リソースが定義される THEN THE CDK SHALL CfnRuntime（L1）を使用して AWS::BedrockAgentCore::Runtime を作成する
2. WHEN Runtime が作成される THEN THE Runtime SHALL AgentRuntimeArtifact（S3 URI または ContainerImage）を指定する
3. WHEN Runtime が作成される THEN THE Runtime SHALL NetworkConfiguration（PUBLIC または VPC）を指定する
4. WHEN ライフサイクル設定が必要な場合 THEN THE Runtime SHALL LifecycleConfiguration でタイムアウトを設定する
5. WHEN RuntimeEndpoint が必要な場合 THEN THE CDK SHALL CfnRuntimeEndpoint を使用してエンドポイントを作成する

### Requirement 2: Gateway 設定

**User Story:** As a 開発者, I want to AgentCore Gateway を CDK で定義する, so that MCP 経由で外部ツールに接続できる。

#### Acceptance Criteria

1. WHEN Gateway リソースが定義される THEN THE CDK SHALL CfnGateway（L1）を使用して AWS::BedrockAgentCore::Gateway を作成する
2. WHEN Gateway が作成される THEN THE Gateway SHALL AuthorizerType（CUSTOM_JWT、AWS_IAM、NONE）を指定する
3. WHEN Gateway が作成される THEN THE Gateway SHALL ProtocolType（MCP）を指定する
4. WHEN GatewayTarget が必要な場合 THEN THE CDK SHALL CfnGatewayTarget を使用してターゲットを作成する
5. WHEN GatewayTarget が作成される THEN THE GatewayTarget SHALL TargetConfiguration と CredentialProviderConfigurations を指定する

### Requirement 3: Memory 設定

**User Story:** As a 開発者, I want to AgentCore Memory を CDK で定義する, so that エージェントが過去の情報を活用できる。

#### Acceptance Criteria

1. WHEN Memory リソースが定義される THEN THE CDK SHALL CfnMemory（L1）を使用して AWS::BedrockAgentCore::Memory を作成する
2. WHEN Memory が作成される THEN THE Memory SHALL Name と EventExpiryDuration（7-365 日）を指定する
3. WHEN Memory 戦略が必要な場合 THEN THE Memory SHALL MemoryStrategies を設定する
4. WHEN 暗号化が必要な場合 THEN THE Memory SHALL EncryptionKeyArn を指定する

### Requirement 4: WorkloadIdentity 設定

**User Story:** As a 開発者, I want to AgentCore WorkloadIdentity を CDK で定義する, so that OAuth2 ベースの認証を提供できる。

#### Acceptance Criteria

1. WHEN WorkloadIdentity リソースが定義される THEN THE CDK SHALL CfnWorkloadIdentity（L1）を使用して AWS::BedrockAgentCore::WorkloadIdentity を作成する
2. WHEN WorkloadIdentity が作成される THEN THE WorkloadIdentity SHALL Name を指定する
3. WHEN OAuth2 リターン URL が必要な場合 THEN THE WorkloadIdentity SHALL AllowedResourceOauth2ReturnUrls を設定する

### Requirement 5: Strands Agents 連携

**User Story:** As a 開発者, I want to Strands Agents SDK と AgentCore を連携する, so that 型安全なエージェントを実行できる。

#### Acceptance Criteria

1. WHEN エージェントが定義される THEN THE Strands_Agents SHALL Pydantic スキーマによる型安全なツール定義をサポートする
2. WHEN エージェントが AgentCore にデプロイされる THEN THE Runtime SHALL Strands Agents 形式のエージェントを実行する
3. WHEN Bedrock モデルが呼び出される THEN THE Strands_Agents SHALL Nova 2 Lite モデルを使用する

### Requirement 6: CDK 統合

**User Story:** As a 開発者, I want to AgentCore リソースを CDK で定義する, so that インフラをコードで管理できる。

#### Acceptance Criteria

1. WHEN AgentCore リソースが定義される THEN THE CDK SHALL L1（CfnXxx）リソースを使用する（L2 が存在しないため）
2. WHEN 検証環境にデプロイされる THEN THE CDK SHALL リソースの一括削除を可能にする設定を適用する
3. WHEN IAM ロールが必要な場合 THEN THE CDK SHALL bedrock-agentcore.amazonaws.com を信頼するロールを作成する
