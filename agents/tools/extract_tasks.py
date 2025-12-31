"""
タスク抽出ツール

議事録からアクションアイテム（タスク）を抽出するツール。
Strands Agents SDK の @tool デコレータを使用。
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from strands import tool


class TaskItem(BaseModel):
    """タスクアイテムのスキーマ"""
    
    title: str = Field(
        ...,
        description="タスクのタイトル",
        min_length=1,
    )
    description: Optional[str] = Field(
        default=None,
        description="タスクの詳細説明",
    )
    assignee: Optional[str] = Field(
        default=None,
        description="担当者",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="期限（YYYY-MM-DD形式）",
    )
    priority: str = Field(
        default="medium",
        description="優先度（high/medium/low）",
    )
    labels: list[str] = Field(
        default_factory=list,
        description="ラベルリスト",
    )


class ExtractedTasks(BaseModel):
    """抽出されたタスクリストのスキーマ"""
    
    tasks: list[TaskItem] = Field(
        default_factory=list,
        description="抽出されたタスクリスト",
    )
    source_type: str = Field(
        default="meeting_minutes",
        description="ソースの種類",
    )
    extraction_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="抽出日時",
    )


@tool
def extract_tasks(
    meeting_minutes: str,
    default_assignee: Optional[str] = None,
    default_due_days: int = 7,
) -> dict:
    """
    議事録からアクションアイテム（タスク）を抽出する。
    
    このツールは議事録テキストを分析し、アクションアイテムを
    構造化されたタスクリストとして抽出します。
    GitHub Issues への登録に適した形式で出力します。
    
    Args:
        meeting_minutes: 議事録テキスト
        default_assignee: デフォルトの担当者（オプション）
        default_due_days: デフォルトの期限日数（デフォルト: 7日）
    
    Returns:
        dict: 抽出されたタスク情報
            - success: 処理成功フラグ
            - tasks: タスクリスト
            - task_count: タスク数
            - github_issues_format: GitHub Issues 形式のタスク
    """
    # 入力バリデーション
    if not meeting_minutes or len(meeting_minutes.strip()) < 10:
        return {
            "success": False,
            "error": "議事録テキストが短すぎます。最低10文字以上必要です。",
            "tasks": [],
            "task_count": 0,
        }
    
    # タスク抽出のヒントを提供
    extraction_hints = _generate_extraction_hints(meeting_minutes)
    
    # デフォルト期限を計算
    default_due_date = _calculate_default_due_date(default_due_days)
    
    return {
        "success": True,
        "extraction_hints": extraction_hints,
        "default_settings": {
            "assignee": default_assignee,
            "due_date": default_due_date,
            "due_days": default_due_days,
        },
        "instructions": (
            "議事録から以下のパターンでタスクを抽出してください：\n"
            "1. 「〜する」「〜を行う」などの動詞で終わる文\n"
            "2. 担当者が明記されている項目\n"
            "3. 期限が設定されている項目\n"
            "4. 「TODO」「アクション」「対応」などのキーワードを含む項目\n\n"
            "各タスクには以下の情報を含めてください：\n"
            "- title: タスクのタイトル\n"
            "- description: 詳細説明\n"
            "- assignee: 担当者\n"
            "- due_date: 期限（YYYY-MM-DD形式）\n"
            "- priority: 優先度（high/medium/low）\n"
            "- labels: 関連ラベル"
        ),
        "output_format": {
            "tasks": [
                {
                    "title": "タスクタイトル",
                    "description": "タスクの詳細説明",
                    "assignee": "担当者名",
                    "due_date": "YYYY-MM-DD",
                    "priority": "high|medium|low",
                    "labels": ["label1", "label2"],
                }
            ]
        },
        "github_issue_template": _generate_github_issue_template(),
    }


def _generate_extraction_hints(text: str) -> dict:
    """
    テキストからタスク抽出のヒントを生成する。
    
    Args:
        text: 議事録テキスト
    
    Returns:
        dict: 抽出ヒント
    """
    # タスク関連のキーワードを検出
    task_keywords = [
        "TODO", "todo", "タスク", "アクション", "対応",
        "確認", "検討", "作成", "実装", "修正", "調査",
        "報告", "連絡", "準備", "手配", "依頼",
    ]
    
    found_keywords = []
    for keyword in task_keywords:
        if keyword in text:
            found_keywords.append(keyword)
    
    # 担当者パターンを検出
    assignee_patterns = [
        "担当:", "担当：", "→", "⇒", "さん",
    ]
    
    has_assignee_hints = any(pattern in text for pattern in assignee_patterns)
    
    # 期限パターンを検出
    deadline_patterns = [
        "期限:", "期限：", "まで", "締切", "〆切",
        "月", "日", "週",
    ]
    
    has_deadline_hints = any(pattern in text for pattern in deadline_patterns)
    
    return {
        "found_task_keywords": found_keywords,
        "has_assignee_hints": has_assignee_hints,
        "has_deadline_hints": has_deadline_hints,
        "text_length": len(text),
        "estimated_task_count": len(found_keywords),
    }


def _calculate_default_due_date(days: int) -> str:
    """
    デフォルトの期限日を計算する。
    
    Args:
        days: 日数
    
    Returns:
        str: YYYY-MM-DD形式の日付
    """
    from datetime import timedelta
    due_date = datetime.now() + timedelta(days=days)
    return due_date.strftime("%Y-%m-%d")


def _generate_github_issue_template() -> str:
    """
    GitHub Issue のテンプレートを生成する。
    
    Returns:
        str: GitHub Issue テンプレート
    """
    return """## タスク概要
{description}

## 背景
- 会議: {meeting_title}
- 日時: {meeting_date}

## 完了条件
- [ ] {acceptance_criteria}

## 関連情報
- 担当者: @{assignee}
- 期限: {due_date}
- 優先度: {priority}

---
*このIssueは議事録から自動生成されました*
"""


def format_task_for_github(task: TaskItem, meeting_info: Optional[dict] = None) -> dict:
    """
    タスクを GitHub Issue 形式にフォーマットする。
    
    Args:
        task: タスクアイテム
        meeting_info: 会議情報（オプション）
    
    Returns:
        dict: GitHub Issue 形式のデータ
    """
    meeting_info = meeting_info or {}
    
    body = f"""## タスク概要
{task.description or task.title}

## 背景
- 会議: {meeting_info.get('title', '不明')}
- 日時: {meeting_info.get('date', '不明')}

## 完了条件
- [ ] タスクを完了する

## 関連情報
- 担当者: {task.assignee or '未定'}
- 期限: {task.due_date or '未定'}
- 優先度: {task.priority}

---
*このIssueは議事録から自動生成されました*
"""
    
    return {
        "title": task.title,
        "body": body,
        "assignees": [task.assignee] if task.assignee else [],
        "labels": task.labels + [f"priority:{task.priority}"],
    }
