"""
GitHub連携データモデル

GitHub Issues作成機能で使用するデータモデルを定義する。
Requirements: 2.1, 2.2, 2.3
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """
    タスク優先度
    
    タスクの優先度を表現する。
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(BaseModel):
    """
    タスク（入力）
    
    承認済みタスクから抽出された情報を表現する。
    GitHub Issueの作成元となるデータモデル。
    Requirements: 2.1, 2.2, 2.3
    """
    
    title: str = Field(
        ...,
        description="タスクタイトル",
        min_length=1,
        max_length=100,
    )
    description: str = Field(
        ...,
        description="タスクの説明",
        min_length=1,
    )
    assignee: Optional[str] = Field(
        default=None,
        description="担当者名（「未定」の場合あり）",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="期限（「未定」の場合あり）",
    )
    priority: Priority = Field(
        ...,
        description="優先度（high/medium/low）",
    )
    source_minutes_url: str = Field(
        ...,
        description="元の議事録URL",
    )


class IssueRequest(BaseModel):
    """
    Issue作成リクエスト
    
    GitHub APIに送信するIssue作成リクエストを表現する。
    """
    
    title: str = Field(
        ...,
        description="Issueタイトル",
        max_length=256,
    )
    body: str = Field(
        ...,
        description="Issue本文",
        max_length=65536,
    )
    labels: list[str] = Field(
        default_factory=list,
        description="ラベルリスト",
    )
    assignees: list[str] = Field(
        default_factory=list,
        description="担当者リスト（GitHubユーザー名）",
    )
    milestone: Optional[int] = Field(
        default=None,
        description="マイルストーン番号",
    )


class IssueResult(BaseModel):
    """
    Issue作成結果
    
    GitHub Issue作成の結果を表現する。
    Requirements: 2.6, 7.2, 7.3
    """
    
    task_title: str = Field(
        ...,
        description="元のタスクタイトル",
    )
    success: bool = Field(
        ...,
        description="成功/失敗",
    )
    issue_url: Optional[str] = Field(
        default=None,
        description="作成されたIssueのURL",
    )
    issue_number: Optional[int] = Field(
        default=None,
        description="Issue番号",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="エラーメッセージ（失敗時）",
    )
