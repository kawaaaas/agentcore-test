# インフラ基盤 要件定義

## 概要

議事録・タスク管理自動化 AI エージェントの基盤となる AWS インフラストラクチャを構築する。
CDK を使用して IaC で管理し、検証環境として一括削除可能な設計とする。

## 用語集（Glossary）

- **CDK_App**: AWS CDK アプリケーション全体を管理するエントリーポイント
- **Main_Stack**: すべての Construct を組み合わせるメインスタック
- **Storage_Construct**: S3 バケットや DynamoDB テーブルを管理する Construct
- **Transcript_Bucket**: 会議の書き起こしテキストを保存する S3 バケット
- **Minutes_Bucket**: 生成された議事録を保存する S3 バケット
- **Session_Table**: エージェントのセッション状態を保存する DynamoDB テーブル
- **EventBridge_Rule**: S3 イベントを検知してエージェントを起動するルール

## 要件

### 要件 1: CDK プロジェクトの初期化

**ユーザーストーリー:** 開発者として、TypeScript ベースの CDK プロジェクトを初期化したい。これにより、インフラをコードで管理できるようになる。

#### 受け入れ条件

1. THE CDK_App SHALL TypeScript で実装される
2. THE CDK_App SHALL Biome によるフォーマットとリンターの設定を含む
3. THE CDK_App SHALL Jest によるテスト環境を含む
4. WHEN `cdk deploy` を実行した場合、THE Main_Stack SHALL 正常にデプロイされる
5. WHEN `cdk synth` を実行した場合、THE CDK_App SHALL 有効な CloudFormation テンプレートを生成する

### 要件 2: ストレージリソースの作成

**ユーザーストーリー:** 開発者として、書き起こしテキストと議事録を保存するためのストレージを作成したい。これにより、エージェントがデータを永続化できるようになる。

#### 受け入れ条件

1. THE Storage_Construct SHALL Transcript_Bucket を作成する
2. THE Storage_Construct SHALL Minutes_Bucket を作成する
3. WHEN S3 バケットが作成される場合、THE Storage_Construct SHALL `removalPolicy: DESTROY` と `autoDeleteObjects: true` を設定する
4. THE Storage_Construct SHALL Session_Table を作成する
5. WHEN DynamoDB テーブルが作成される場合、THE Storage_Construct SHALL `removalPolicy: DESTROY` を設定する
6. THE Storage_Construct SHALL 可能な限り L2 コンストラクトを使用する
7. THE Session_Table SHALL パーティションキーとして `sessionId` を持つ

### 要件 3: イベント駆動トリガーの設定

**ユーザーストーリー:** 開発者として、S3 への書き起こしテキストのアップロードをトリガーにエージェントを起動したい。これにより、自動的に議事録生成が開始される。

#### 受け入れ条件

1. WHEN 書き起こしテキストが Transcript_Bucket にアップロードされた場合、THE Main_Stack SHALL EventBridge ルールをトリガーする
2. THE Main_Stack SHALL EventBridge_Rule を作成する
3. THE EventBridge_Rule SHALL S3 の PutObject イベントをフィルタリングする
4. THE Transcript_Bucket SHALL EventBridge 通知を有効化する

### 要件 4: 一括削除機能

**ユーザーストーリー:** 開発者として、検証環境のリソースを一括で削除したい。これにより、クリーンアップが容易になる。

#### 受け入れ条件

1. WHEN `cdk destroy`を実行した場合、THE Main_Stack SHALL すべてのリソースを削除する
2. THE Main_Stack SHALL 削除保護を無効化した状態でリソースを作成する
3. IF S3 バケットにオブジェクトが存在する場合、THEN THE Storage_Construct SHALL オブジェクトを自動削除してからバケットを削除する

### 要件 5: スタック分割と Construct 設計

**ユーザーストーリー:** 開発者として、関心ごとに分離された Construct 構造を持ちたい。これにより、コードの保守性と拡張性が向上する。

#### 受け入れ条件

1. THE Main_Stack SHALL 単一責任の原則に従った Construct に分割される
2. THE Storage_Construct SHALL ストレージリソースのみを管理する
3. WHEN 新しい機能を追加する場合、THE Main_Stack SHALL 新しい Construct を追加することで対応できる
4. THE CDK_App SHALL 以下のディレクトリ構造に従う:
   - `lib/stacks/` - スタック定義
   - `lib/constructs/` - Construct 定義
   - `bin/` - CDK アプリエントリーポイント

## 制約事項

- AWS CDK v2 を使用する
- TypeScript で実装する
- L2 コンストラクトを優先的に使用する（L1 は最終手段）
- 検証環境のため、本番環境向けのセキュリティ設定は最小限とする
