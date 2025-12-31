# AI・AWS ツール利用ガイドライン

## Kiro Powers 活用ルール

### CDK 実装時（必須）

CDK コードを実装する際は、**必ず** `aws-infrastructure-as-code` Power を有効化して問い合わせる。

確認すべき内容:

- L2 コンストラクトの最新 API
- ベストプラクティス
- CloudFormation テンプレートの検証

### Bedrock 実装時（必須）

Bedrock を使用するコードを実装する際は、**必ず** AWS 関連の Power を有効化して問い合わせる。

確認すべき内容:

- Nova 2 Lite の最新仕様
- Bedrock API の使用方法
- AgentCore 連携のベストプラクティス

### AgentCore 実装時（必須）

AgentCore は 2025 年最新のサービスのため、**必ず** `aws-agentcore` Power を有効化して最新情報を確認する。

確認すべき内容:

- Runtime、Gateway、Identity の設定方法
- Strands Agents との連携
- MCP 統合の実装方法

## 最新情報の確認

このプロジェクトは最新の AWS サービスを使用するため:

1. **実装前**: 該当サービスの最新ドキュメントを確認
2. **不明点**: Web 検索や AWS Power で最新情報を取得
3. **リージョン対応**: AgentCore の利用可能リージョンを確認

## 参照すべきリソース

- [Strands Agents SDK](https://github.com/strands-agents/sdk-ts)
- [AWS AgentCore Documentation](https://docs.aws.amazon.com/agentcore/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [MCP Specification](https://modelcontextprotocol.io/)
