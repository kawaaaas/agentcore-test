"""
議事録要約ツール

会議の書き起こしテキストから議事録を生成するツール。
Strands Agents SDK の @tool デコレータを使用。
"""

from typing import Optional
from pydantic import BaseModel, Field
from strands import tool


class MeetingTranscript(BaseModel):
    """会議書き起こしの入力スキーマ"""
    
    transcript: str = Field(
        ...,
        description="会議の書き起こしテキスト",
        min_length=10,
    )
    meeting_date: Optional[str] = Field(
        default=None,
        description="会議日時（YYYY-MM-DD形式）",
    )
    participants: Optional[list[str]] = Field(
        default=None,
        description="参加者リスト",
    )
    meeting_title: Optional[str] = Field(
        default=None,
        description="会議タイトル",
    )


class MeetingMinutes(BaseModel):
    """議事録の出力スキーマ"""
    
    title: str = Field(
        ...,
        description="会議タイトル",
    )
    date: Optional[str] = Field(
        default=None,
        description="会議日時",
    )
    participants: list[str] = Field(
        default_factory=list,
        description="参加者リスト",
    )
    summary: str = Field(
        ...,
        description="会議の要約",
    )
    agenda_items: list[str] = Field(
        default_factory=list,
        description="議題リスト",
    )
    decisions: list[str] = Field(
        default_factory=list,
        description="決定事項リスト",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="次のステップ・アクション",
    )
    raw_minutes: str = Field(
        ...,
        description="整形された議事録テキスト",
    )


@tool
def summarize_meeting(
    transcript: str,
    meeting_date: Optional[str] = None,
    participants: Optional[list[str]] = None,
    meeting_title: Optional[str] = None,
) -> dict:
    """
    会議の書き起こしテキストから議事録を生成する。
    
    このツールは会議の書き起こしを分析し、構造化された議事録を作成します。
    議題、決定事項、次のステップを抽出して整理します。
    
    Args:
        transcript: 会議の書き起こしテキスト
        meeting_date: 会議日時（オプション、YYYY-MM-DD形式）
        participants: 参加者リスト（オプション）
        meeting_title: 会議タイトル（オプション）
    
    Returns:
        dict: 構造化された議事録データ
            - title: 会議タイトル
            - date: 会議日時
            - participants: 参加者リスト
            - summary: 会議の要約
            - agenda_items: 議題リスト
            - decisions: 決定事項リスト
            - next_steps: 次のステップ
            - raw_minutes: 整形された議事録テキスト
    """
    # 入力バリデーション
    if not transcript or len(transcript.strip()) < 10:
        return {
            "error": "書き起こしテキストが短すぎます。最低10文字以上必要です。",
            "success": False,
        }
    
    # 議事録の基本構造を作成
    # 注: 実際の要約処理はLLMが行うため、ここでは構造化のみ
    minutes = MeetingMinutes(
        title=meeting_title or "会議議事録",
        date=meeting_date,
        participants=participants or [],
        summary="",  # LLMが生成
        agenda_items=[],  # LLMが抽出
        decisions=[],  # LLMが抽出
        next_steps=[],  # LLMが抽出
        raw_minutes="",  # LLMが生成
    )
    
    # 議事録テンプレートを生成
    template = _generate_minutes_template(
        transcript=transcript,
        title=minutes.title,
        date=minutes.date,
        participants=minutes.participants,
    )
    
    return {
        "success": True,
        "template": template,
        "transcript_length": len(transcript),
        "metadata": {
            "title": minutes.title,
            "date": minutes.date,
            "participants": minutes.participants,
        },
        "instructions": (
            "上記のテンプレートを使用して、書き起こしから以下を抽出してください：\n"
            "1. 会議の要約（3-5文）\n"
            "2. 議題と議論内容\n"
            "3. 決定事項\n"
            "4. アクションアイテム（担当者・期限付き）\n"
            "5. 次回予定"
        ),
    }


def _generate_minutes_template(
    transcript: str,
    title: str,
    date: Optional[str],
    participants: list[str],
) -> str:
    """
    議事録のテンプレートを生成する。
    
    Args:
        transcript: 書き起こしテキスト
        title: 会議タイトル
        date: 会議日時
        participants: 参加者リスト
    
    Returns:
        str: 議事録テンプレート
    """
    participants_str = "、".join(participants) if participants else "（参加者を抽出してください）"
    date_str = date or "（日時を抽出してください）"
    
    template = f"""# {title}

## 会議情報
- 日時: {date_str}
- 参加者: {participants_str}

## 会議の要約
（書き起こしから要約を生成してください）

## 議題と議論内容
（書き起こしから議題を抽出してください）

## 決定事項
（書き起こしから決定事項を抽出してください）

## アクションアイテム
| 担当者 | タスク | 期限 |
|--------|--------|------|
| （抽出） | （抽出） | （抽出） |

## 次回予定
（書き起こしから次回予定を抽出してください）

---
書き起こし文字数: {len(transcript)}文字
"""
    return template
