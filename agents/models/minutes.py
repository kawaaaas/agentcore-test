"""
議事録データモデル

会議の議事録を表現するデータモデルを定義する。
Requirements: 2.2, 2.5
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """
    アクションアイテム（タスク）
    
    議事録から抽出されたアクションアイテムを表現する。
    """
    
    description: str = Field(
        ...,
        description="タスクの説明",
        min_length=1,
    )
    assignee: Optional[str] = Field(
        default=None,
        description="担当者名",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="期限（YYYY-MM-DD形式）",
    )
    completed: bool = Field(
        default=False,
        description="完了フラグ",
    )


class Minutes(BaseModel):
    """
    議事録
    
    会議の議事録を表現するメインデータモデル。
    Requirements: 2.2
    """
    
    title: str = Field(
        ...,
        description="会議タイトル",
        min_length=1,
    )
    date: datetime = Field(
        ...,
        description="会議日時",
    )
    participants: List[str] = Field(
        default_factory=list,
        description="参加者リスト",
    )
    agenda: List[str] = Field(
        default_factory=list,
        description="議題リスト",
    )
    discussion: str = Field(
        ...,
        description="議論内容",
        min_length=1,
    )
    decisions: List[str] = Field(
        default_factory=list,
        description="決定事項リスト",
    )
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="アクションアイテムリスト",
    )


class MinutesMetadata(BaseModel):
    """
    議事録メタデータ
    
    S3保存時に付与するメタデータ。
    Requirements: 5.3
    """
    
    generated_at: datetime = Field(
        ...,
        description="生成日時",
    )
    source_file: str = Field(
        ...,
        description="元の書き起こしファイル名",
    )
    approver: Optional[str] = Field(
        default=None,
        description="承認者",
    )
    session_id: str = Field(
        ...,
        description="AgentCoreセッションID",
    )
