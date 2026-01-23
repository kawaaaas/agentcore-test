"""
Meeting Agent - 議事録生成・タスク抽出エージェント

AWS AgentCore と Strands Agents SDK を使用した
議事録の要約とタスク抽出を行うエージェント。

Requirements: 2.1
"""

import os
import logging
from typing import Optional
from datetime import datetime

import boto3
from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient, MemorySessionManager

# ツールのインポート
from agents.tools.generator import generate_minutes
from agents.tools.extract_tasks import extract_tasks_from_minutes
from agents.tools.validate import validate_transcript
from agents.tools.formatter import MinutesFormatter
from agents.tools.slack_notifier import send_slack_approval_message
from agents.tools.github_tools import (
    create_github_issue,
    create_github_issues_batch,
    check_duplicate_issue,
)
from agents.models.minutes import Minutes, MinutesMetadata

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AgentCore Runtime アプリケーション初期化
app = BedrockAgentCoreApp()

# システムプロンプト定義
# Requirements: 2.1
SYSTEM_PROMPT = """あなたは議事録生成とタスク抽出を専門とするAIアシスタントです。

## 役割
- 会議の書き起こしテキストから議事録を生成する
- 議事録からアクションアイテム（タスク）を抽出する
- ユーザーの修正指示に基づいて内容を改善する
- 過去の修正パターンを学習し、同様の改善を自動的に適用する
- 生成した議事録やタスクを Slack で承認依頼する
- 承認されたタスクを GitHub Issues に自動登録する

## 出力形式
議事録は以下の構造化された形式で生成してください：
1. 会議タイトル
2. 日時
3. 参加者リスト
4. 議題
5. 議論内容（要約）
6. 決定事項
7. アクションアイテム（担当者、期限付き）

## 注意事項
- 簡潔かつ正確に情報を整理する（Requirements 2.3, 2.4）
- 重要なポイントを抽出し、冗長な表現を簡潔にまとめる
- タスクには必ず担当者と期限を明記する
- 参加者情報が不明な場合は空のリストを返す（Requirements 2.5）
- 不明確な点は確認を求める

## GitHub Issue 登録フロー
タスク承認後の Issue 登録フローは以下の通りです：
1. タスクが承認されたら、重複チェックを実行する（check_duplicate_issue）
2. 重複が検出された場合は、Slack で警告を表示し、ユーザーに確認を求める
3. 重複がない、またはユーザーが登録を承認した場合、Issue を作成する
4. 単一タスクの場合は create_github_issue を使用
5. 複数タスクの場合は create_github_issues_batch を使用
6. 登録完了後、Issue URL を含む完了メッセージを Slack に送信する

## 利用可能なツール
- validate_transcript: 書き起こしテキストの検証
- generate_minutes: 議事録の生成
- extract_tasks_from_minutes: タスクの抽出
- send_slack_approval_message: Slack への承認メッセージ送信
- check_duplicate_issue: GitHub Issue の重複チェック
- create_github_issue: 単一 GitHub Issue の作成
- create_github_issues_batch: 複数 GitHub Issue の一括作成
"""

# Nova 2 Lite モデル設定
# Amazon Bedrock の Nova 2 Lite モデルを使用（コストパフォーマンス重視）
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

# AgentCore Memory 設定
# Requirements: 7.1, 7.2, 7.4, 7.5
MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID")
MEMORY_ENABLED = os.getenv("AGENTCORE_MEMORY_ENABLED", "true").lower() == "true"

# S3 バケット設定
# Requirements: 5.1, 5.3
MINUTES_BUCKET_NAME = os.getenv("MINUTES_BUCKET_NAME")


def save_minutes_to_s3(
    minutes: Minutes,
    session_id: str,
    source_file: str,
    approver: Optional[str] = None,
    bucket_name: Optional[str] = None,
) -> str:
    """
    承認された議事録をS3に保存する。
    
    Requirements: 5.1, 5.3
    
    Args:
        minutes: 議事録オブジェクト
        session_id: AgentCoreセッションID
        source_file: 元の書き起こしファイル名
        approver: 承認者（オプション）
        bucket_name: S3バケット名（オプション、環境変数から取得）
    
    Returns:
        S3オブジェクトキー
    
    Raises:
        ValueError: バケット名が設定されていない場合
        Exception: S3保存に失敗した場合
    """
    # バケット名の取得
    bucket = bucket_name or MINUTES_BUCKET_NAME
    if not bucket:
        raise ValueError("MINUTES_BUCKET_NAME が設定されていません")
    
    try:
        # Formatterを使用してMarkdown形式に変換
        formatter = MinutesFormatter()
        markdown_content = formatter.to_markdown(minutes)
        
        # ファイル名を生成 (Requirement 5.2)
        filename = formatter.generate_filename(minutes)
        
        # S3クライアントを初期化
        s3_client = boto3.client("s3", region_name=AWS_REGION)
        
        # メタデータを作成 (Requirement 5.3)
        metadata = MinutesMetadata(
            generated_at=datetime.now(),
            source_file=source_file,
            approver=approver,
            session_id=session_id,
        )
        
        # S3にアップロード
        # メタデータをS3オブジェクトメタデータとして付与
        s3_metadata = {
            "generated-at": metadata.generated_at.isoformat(),
            "source-file": metadata.source_file,
            "session-id": metadata.session_id,
        }
        if metadata.approver:
            s3_metadata["approver"] = metadata.approver
        
        s3_client.put_object(
            Bucket=bucket,
            Key=filename,
            Body=markdown_content.encode("utf-8"),
            ContentType="text/markdown; charset=utf-8",
            Metadata=s3_metadata,
        )
        
        logger.info(f"議事録をS3に保存しました: s3://{bucket}/{filename}")
        logger.info(f"メタデータ: {s3_metadata}")
        
        return filename
        
    except Exception as e:
        logger.error(f"S3保存エラー: {e}")
        raise Exception(f"議事録のS3保存に失敗しました: {str(e)}") from e



def create_memory_session_manager() -> Optional[MemorySessionManager]:
    """
    AgentCore Memory Session Manager を作成する。
    
    Requirements: 7.1, 7.2, 7.4, 7.5
    
    Memory の使い分け:
    - STM (Short-term Memory): 承認フロー中の会話、承認待ち議事録本体
    - LTM (Long-term Memory): 修正パターン、ユーザーの好み
    
    Returns:
        MemorySessionManager: Memory Session Manager、またはNone（Memory無効時）
    """
    if not MEMORY_ENABLED:
        logger.info("AgentCore Memory は無効化されています")
        return None
    
    if not MEMORY_ID:
        logger.warning("AGENTCORE_MEMORY_ID が設定されていません。Memory機能は利用できません。")
        return None
    
    try:
        # Memory Session Managerを作成
        # Requirements: 7.1, 7.2, 7.4, 7.5
        session_manager = MemorySessionManager(
            memory_id=MEMORY_ID,
            region_name=AWS_REGION,
        )
        
        logger.info(f"AgentCore Memory Session Manager を設定しました (memory_id={MEMORY_ID})")
        logger.info("STM: 承認フロー中の会話、承認待ち議事録")
        logger.info("LTM: 修正パターン、ユーザーの好み")
        
        return session_manager
    except Exception as e:
        logger.error(f"AgentCore Memory Session Manager の初期化に失敗しました: {e}")
        return None


def create_memory_client() -> Optional[MemoryClient]:
    """
    AgentCore Memory クライアントを作成する。
    
    Requirements: 7.1, 7.2, 7.4, 7.5
    
    Returns:
        MemoryClient: Memoryクライアント、またはNone（Memory無効時）
    """
    if not MEMORY_ENABLED:
        logger.info("AgentCore Memory は無効化されています")
        return None
    
    try:
        client = MemoryClient(region_name=AWS_REGION)
        logger.info("AgentCore Memory クライアントを初期化しました")
        return client
    except Exception as e:
        logger.error(f"AgentCore Memory クライアントの初期化に失敗しました: {e}")
        return None


def create_agent() -> Agent:
    """
    Meeting Agent を作成する。
    
    Requirements: 2.1, 6.1, 6.3, 6.4
    
    ツールを登録:
    - validate_transcript: 書き起こしテキストの検証
    - generate_minutes: 議事録の生成
    - extract_tasks_from_minutes: タスクの抽出
    - send_slack_approval_message: Slack 承認メッセージの送信
    - check_duplicate_issue: GitHub Issue の重複チェック
    - create_github_issue: 単一 GitHub Issue の作成
    - create_github_issues_batch: 複数 GitHub Issue の一括作成
    
    Returns:
        Agent: 設定済みの Strands Agent インスタンス
    """
    # エージェントを作成
    # Strands Agents SDK はモデルIDを直接指定
    agent = Agent(
        model=MODEL_ID,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            generate_minutes,
            extract_tasks_from_minutes,
            send_slack_approval_message,
            check_duplicate_issue,
            create_github_issue,
            create_github_issues_batch,
        ],
    )
    
    logger.info(f"Meeting Agent を初期化しました (model={MODEL_ID}, region={AWS_REGION})")
    logger.info(
        f"登録ツール: generate_minutes, extract_tasks_from_minutes, "
        f"send_slack_approval_message, check_duplicate_issue, "
        f"create_github_issue, create_github_issues_batch"
    )
    return agent


# グローバルエージェントインスタンス
_agent: Optional[Agent] = None


def get_agent() -> Agent:
    """
    シングルトンパターンでエージェントを取得する。
    
    Returns:
        Agent: Meeting Agent インスタンス
    """
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


@app.entrypoint
def agent_invocation(payload: dict, context) -> dict:
    """
    AgentCore Runtime からの呼び出しエントリポイント。
    
    Args:
        payload: リクエストペイロード
            - prompt: ユーザーからの入力テキスト
            - transcript: 会議の書き起こしテキスト（オプション）
        context: AgentCore Runtime コンテキスト
    
    Returns:
        dict: エージェントの応答
            - result: 応答メッセージ
            - session_id: セッションID
    """
    # ユーザー入力を取得
    user_message = payload.get(
        "prompt",
        "入力が見つかりません。会議の書き起こしテキストを提供してください。"
    )
    
    # 書き起こしテキストがある場合は追加
    transcript = payload.get("transcript")
    if transcript:
        user_message = f"以下の会議書き起こしから議事録を作成してください：\n\n{transcript}"
    
    logger.info(f"リクエスト受信: {user_message[:100]}...")
    
    # エージェントを実行
    agent = get_agent()
    result = agent(user_message)
    
    # セッションIDを取得（存在する場合）
    session_id = getattr(context, "session_id", "default")
    
    logger.info(f"応答生成完了 (session_id={session_id})")
    
    return {
        "result": result.message,
        "session_id": session_id,
    }


# ローカル実行用
if __name__ == "__main__":
    app.run()
