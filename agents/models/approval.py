"""
承認フローデータモデル

Slack承認フローで使用するデータモデルを定義する。
Requirements: 4.3, 4.4
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """
    承認ステータス
    
    議事録の承認状態を表現する。
    """
    
    PENDING = "pending"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    EXPIRED = "expired"


class PendingMinutesRecord(BaseModel):
    """
    承認待ち議事録レコード（DynamoDB用）
    
    承認待ち状態の議事録のメタデータをDynamoDBに保存する。
    Requirements: 4.3, 4.4
    """
    
    session_id: str = Field(
        ...,
        description="AgentCoreセッションID（パーティションキー）",
    )
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING,
        description="承認ステータス",
    )
    created_at: datetime = Field(
        ...,
        description="作成日時",
    )
    updated_at: datetime = Field(
        ...,
        description="更新日時",
    )
    slack_message_ts: Optional[str] = Field(
        default=None,
        description="Slackメッセージのタイムスタンプ",
    )
    slack_channel_id: Optional[str] = Field(
        default=None,
        description="SlackチャンネルID",
    )
    memory_blob_id: str = Field(
        ...,
        description="AgentCore Memoryに保存された議事録本体のBlob ID",
    )
    revision_count: int = Field(
        default=0,
        description="修正回数",
    )
    expires_at: datetime = Field(
        ...,
        description="有効期限（24時間後）",
    )


class PendingMinutesBlob(BaseModel):
    """
    承認待ち議事録本体（AgentCore Memory用）
    
    承認待ち状態の議事録本体をAgentCore Memory STMに保存する。
    Requirements: 7.5
    """
    
    session_id: str = Field(
        ...,
        description="AgentCoreセッションID",
    )
    minutes_json: str = Field(
        ...,
        description="議事録のJSON文字列（Minutesオブジェクトをシリアライズ）",
    )
    source_transcript: str = Field(
        ...,
        description="元の書き起こしテキスト",
    )
    revision_history: list[str] = Field(
        default_factory=list,
        description="修正履歴（ユーザーからの修正指示）",
    )
