"""
タスク抽出データモデル

タスク抽出機能で使用するデータモデルを定義する。
Requirements: 2.1, 2.2, 2.4, 2.5
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """
    タスク優先度
    
    タスクの優先度を表現する。
    Requirements: 2.6
    """
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(BaseModel):
    """
    タスク
    
    議事録から抽出された個別のタスクを表現する。
    Requirements: 2.1, 2.2, 2.4, 2.5
    """
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="タスクID（UUID）",
    )
    title: str = Field(
        ...,
        description="タイトル（100文字以内）",
        min_length=1,
        max_length=100,
    )
    description: str = Field(
        ...,
        description="説明（議事録からの引用含む）",
        min_length=1,
    )
    assignee: Optional[str] = Field(
        default=None,
        description="担当者（未定の場合None）",
    )
    due_date: Optional[date] = Field(
        default=None,
        description="期限（未定の場合None）",
    )
    priority: Priority = Field(
        ...,
        description="優先度（high/medium/low）",
    )
    source_quote: str = Field(
        ...,
        description="元の議事録の該当箇所",
        min_length=1,
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="作成日時",
    )


class TaskListStatus(str, Enum):
    """
    タスクリストステータス
    
    タスクリストの承認状態を表現する。
    Requirements: 5.3, 5.4
    """
    
    PENDING = "pending"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    CANCELLED = "cancelled"


class TaskList(BaseModel):
    """
    タスクリスト
    
    抽出されたタスクの集合を表現する。
    Requirements: 2.1, 2.2, 2.4, 2.5
    """
    
    session_id: str = Field(
        ...,
        description="AgentCoreセッションID",
    )
    minutes_id: str = Field(
        ...,
        description="元の議事録ID",
    )
    tasks: List[Task] = Field(
        default_factory=list,
        description="タスクリスト",
    )
    status: TaskListStatus = Field(
        default=TaskListStatus.PENDING,
        description="ステータス（pending/approved/revision_requested/cancelled）",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="作成日時",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新日時",
    )
