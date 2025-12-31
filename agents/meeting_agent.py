"""
Meeting Agent - 議事録生成・タスク抽出エージェント

AWS AgentCore と Strands Agents SDK を使用した
議事録の要約とタスク抽出を行うエージェント。
"""

import os
import logging
from typing import Optional

from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# ツールのインポート
from agents.tools import summarize_meeting, extract_tasks

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AgentCore Runtime アプリケーション初期化
app = BedrockAgentCoreApp()

# システムプロンプト定義
SYSTEM_PROMPT = """あなたは議事録生成とタスク抽出を専門とするAIアシスタントです。

## 役割
- 会議の書き起こしテキストから議事録を生成する
- 議事録からアクションアイテム（タスク）を抽出する
- ユーザーの修正指示に基づいて内容を改善する

## 出力形式
議事録は以下の形式で出力してください：
1. 会議概要（日時、参加者、目的）
2. 議題と決定事項
3. アクションアイテム（担当者、期限）
4. 次回予定

## 注意事項
- 簡潔かつ正確に情報を整理する
- 重要な決定事項は漏れなく記録する
- タスクには必ず担当者と期限を明記する
- 不明確な点は確認を求める
"""

# Nova 2 Lite モデル設定
# Amazon Bedrock の Nova 2 Lite モデルを使用（コストパフォーマンス重視）
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")


def create_agent() -> Agent:
    """
    Meeting Agent を作成する。
    
    Returns:
        Agent: 設定済みの Strands Agent インスタンス
    """
    # エージェントを作成
    # Strands Agents SDK はモデルIDを直接指定
    agent = Agent(
        model=MODEL_ID,
        system_prompt=SYSTEM_PROMPT,
        tools=[summarize_meeting, extract_tasks],
    )
    
    logger.info(f"Meeting Agent を初期化しました (model={MODEL_ID}, region={AWS_REGION})")
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
