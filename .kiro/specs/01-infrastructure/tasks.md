# インフラ基盤 実装タスク

## 概要

CDK プロジェクトの初期化から、ストレージリソースと EventBridge ルールの作成までを段階的に実装する。

## タスク

- [ ] 1. CDK プロジェクトの初期化

  - [ ] 1.1 CDK TypeScript プロジェクトを作成する
    - `cdk init app --language typescript` でプロジェクトを初期化
    - 不要なサンプルコードを削除
    - _Requirements: 1.1_
  - [ ] 1.2 Biome の設定を追加する
    - `biome.json` を作成
    - フォーマットとリンターのルールを設定
    - package.json にスクリプトを追加
    - _Requirements: 1.2_
  - [ ] 1.3 Jest テスト環境を設定する
    - `jest.config.js` を確認・調整
    - aws-cdk-lib/assertions を使用するテストの雛形を作成
    - _Requirements: 1.3_

- [ ] 2. ディレクトリ構造の整備

  - [ ] 2.1 設計に従ったディレクトリ構造を作成する
    - `lib/stacks/` ディレクトリを作成
    - `lib/constructs/` ディレクトリを作成
    - 既存の `lib/*.ts` を適切な場所に移動
    - _Requirements: 5.4_

- [ ] 3. Storage Construct の実装

  - [ ] 3.1 StorageConstruct クラスを作成する
    - `lib/constructs/storage-construct.ts` を作成
    - StorageConstructProps インターフェースを定義
    - _Requirements: 5.2_
  - [ ] 3.2 Transcript_Bucket を作成する
    - S3 Bucket L2 コンストラクトを使用
    - `eventBridgeEnabled: true` を設定
    - `removalPolicy: DESTROY` と `autoDeleteObjects: true` を設定
    - _Requirements: 2.1, 2.3, 2.6, 3.4_
  - [ ] 3.3 Minutes_Bucket を作成する
    - S3 Bucket L2 コンストラクトを使用
    - `removalPolicy: DESTROY` と `autoDeleteObjects: true` を設定
    - _Requirements: 2.2, 2.3, 2.6_
  - [ ] 3.4 Session_Table を作成する
    - DynamoDB TableV2 L2 コンストラクトを使用
    - パーティションキー `sessionId` を設定
    - `removalPolicy: DESTROY` を設定
    - _Requirements: 2.4, 2.5, 2.6, 2.7_
  - [ ]\* 3.5 Storage Construct のユニットテストを作成する
    - リソースが正しく作成されることを検証
    - _Requirements: 2.1, 2.2, 2.4_

- [ ] 4. Main Stack の実装

  - [ ] 4.1 MainStack クラスを作成する
    - `lib/stacks/main-stack.ts` を作成
    - StorageConstruct をインスタンス化
    - _Requirements: 5.1_
  - [ ] 4.2 EventBridge ルールを作成する
    - Transcript_Bucket の PutObject イベントをトリガーに設定
    - イベントパターンを定義
    - _Requirements: 3.1, 3.2, 3.3_
  - [ ]\* 4.3 Main Stack のスナップショットテストを作成する
    - CloudFormation テンプレートのスナップショットを検証
    - _Requirements: 1.5_

- [ ] 5. CDK アプリエントリーポイントの更新

  - [ ] 5.1 bin/app.ts を更新する
    - MainStack をインポート
    - 環境設定を追加
    - _Requirements: 1.4_

- [ ] 6. チェックポイント - ビルドとテストの確認

  - `npm run build` でビルドが成功することを確認
  - `npm test` でテストが成功することを確認
  - `cdk synth` で CloudFormation テンプレートが生成されることを確認
  - 問題があればユーザーに確認

- [ ]\* 7. プロパティテストの実装

  - [ ]\* 7.1 削除ポリシーのプロパティテストを作成する
    - **Property 1: ストレージリソースの削除ポリシー設定**
    - **Validates: Requirements 2.3, 2.5, 4.2, 4.3**
    - CloudFormation テンプレートを解析
    - すべての S3 バケットに removalPolicy: DESTROY が設定されていることを検証
    - すべての DynamoDB テーブルに removalPolicy: DESTROY が設定されていることを検証

- [ ] 8. 最終チェックポイント
  - すべてのテストが成功することを確認
  - Biome によるフォーマットとリントが成功することを確認
  - 問題があればユーザーに確認

## 備考

- `*` マークのタスクはオプションであり、MVP では省略可能
- 各タスクは要件との紐付けを明記
- チェックポイントで段階的に検証を行う
- プロパティテストは設計ドキュメントのプロパティを検証
