"""
Block Kit Builder

Slack Block Kit を使用したメッセージ構築ツール。
承認フロー、ステータス更新、リマインダー、モーダルを生成する。

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 6.4
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class BlockType(str, Enum):
    """Block Kit ブロックタイプ"""
    HEADER = "header"
    SECTION = "section"
    DIVIDER = "divider"
    ACTIONS = "actions"
    CONTEXT = "context"
    INPUT = "input"


class ElementType(str, Enum):
    """Block Kit エレメントタイプ"""
    BUTTON = "button"
    PLAIN_TEXT_INPUT = "plain_text_input"
    MRKDWN = "mrkdwn"


class TextType(str, Enum):
    """テキストオブジェクトタイプ"""
    PLAIN_TEXT = "plain_text"
    MRKDWN = "mrkdwn"


class ButtonStyle(str, Enum):
    """ボタンスタイル"""
    PRIMARY = "primary"
    DANGER = "danger"


class ActionType(str, Enum):
    """アクションタイプ"""
    APPROVE = "approve"
    REVISE = "revise"
    CANCEL = "cancel"


class ContentType(str, Enum):
    """コンテンツタイプ"""
    MINUTES = "minutes"
    TASKS = "tasks"


class StatusType(str, Enum):
    """ステータスタイプ"""
    PENDING = "pending"
    APPROVED = "approved"
    REVISING = "revising"
    CANCELLED = "cancelled"
    ERROR = "error"


class TextObject(BaseModel):
    """Block Kit テキストオブジェクト"""
    type: TextType
    text: str
    emoji: Optional[bool] = None


class ButtonElement(BaseModel):
    """Block Kit ボタンエレメント"""
    type: ElementType = ElementType.BUTTON
    text: TextObject
    action_id: str
    value: str
    style: Optional[ButtonStyle] = None


class PlainTextInputElement(BaseModel):
    """Block Kit プレーンテキスト入力エレメント"""
    type: ElementType = ElementType.PLAIN_TEXT_INPUT
    action_id: str
    multiline: bool = True
    placeholder: Optional[TextObject] = None


class HeaderBlock(BaseModel):
    """Block Kit ヘッダーブロック"""
    type: BlockType = BlockType.HEADER
    text: TextObject


class SectionBlock(BaseModel):
    """Block Kit セクションブロック"""
    type: BlockType = BlockType.SECTION
    text: Optional[TextObject] = None
    fields: Optional[List[TextObject]] = None


class DividerBlock(BaseModel):
    """Block Kit ディバイダーブロック"""
    type: BlockType = BlockType.DIVIDER


class ActionsBlock(BaseModel):
    """Block Kit アクションブロック"""
    type: BlockType = BlockType.ACTIONS
    elements: List[ButtonElement]


class ContextBlock(BaseModel):
    """Block Kit コンテキストブロック"""
    type: BlockType = BlockType.CONTEXT
    elements: List[TextObject]


class InputBlock(BaseModel):
    """Block Kit 入力ブロック"""
    type: BlockType = BlockType.INPUT
    block_id: str
    label: TextObject
    element: PlainTextInputElement
    optional: bool = False


class BlockKitBuilder:
    """
    Block Kit メッセージビルダー
    
    Slack Block Kit を使用したインタラクティブメッセージを構築する。
    """
    
    # 文字数制限定数
    MAX_TEXT_LENGTH = 3000  # Slack Block Kit の制限を考慮
    
    @staticmethod
    def _truncate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
        """
        テキストを指定文字数で切り詰める
        
        Requirements: 2.5
        
        Args:
            text: 元のテキスト
            max_length: 最大文字数
            
        Returns:
            切り詰められたテキスト
        """
        if len(text) <= max_length:
            return text
        
        # 切り詰めて省略記号を追加
        truncated = text[:max_length - 20]
        return f"{truncated}...\n\n（文字数制限により省略されました）"
    
    def create_approval_message(
        self,
        session_id: str,
        content_type: ContentType,
        content: str,
        title: str,
    ) -> List[Dict[str, Any]]:
        """
        承認メッセージを生成する
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        
        Args:
            session_id: セッションID
            content_type: コンテンツタイプ（minutes/tasks）
            content: 表示するコンテンツ
            title: タイトル
            
        Returns:
            Block Kit ブロックのリスト
        """
        # 文字数制限処理 (Requirement 2.5)
        truncated_content = self._truncate_text(content)
        
        blocks = []
        
        # ヘッダーブロック
        content_type_label = "議事録" if content_type == ContentType.MINUTES else "タスク"
        header = HeaderBlock(
            text=TextObject(
                type=TextType.PLAIN_TEXT,
                text=f"📋 {content_type_label}の確認",
                emoji=True,
            )
        )
        blocks.append(header.model_dump(exclude_none=True))
        
        # タイトルセクション
        title_section = SectionBlock(
            text=TextObject(
                type=TextType.MRKDWN,
                text=f"*{title}*",
            )
        )
        blocks.append(title_section.model_dump(exclude_none=True))
        
        # ディバイダー
        blocks.append(DividerBlock().model_dump(exclude_none=True))
        
        # コンテンツプレビュー (Requirement 2.1)
        content_section = SectionBlock(
            text=TextObject(
                type=TextType.MRKDWN,
                text=truncated_content,
            )
        )
        blocks.append(content_section.model_dump(exclude_none=True))
        
        # ディバイダー
        blocks.append(DividerBlock().model_dump(exclude_none=True))
        
        # アクションボタン (Requirements 2.2, 2.3, 2.4)
        actions = ActionsBlock(
            elements=[
                ButtonElement(
                    text=TextObject(
                        type=TextType.PLAIN_TEXT,
                        text="✅ 承認",
                        emoji=True,
                    ),
                    action_id=f"{ActionType.APPROVE.value}_{session_id}",
                    value=session_id,
                    style=ButtonStyle.PRIMARY,
                ),
                ButtonElement(
                    text=TextObject(
                        type=TextType.PLAIN_TEXT,
                        text="✏️ 修正",
                        emoji=True,
                    ),
                    action_id=f"{ActionType.REVISE.value}_{session_id}",
                    value=session_id,
                ),
                ButtonElement(
                    text=TextObject(
                        type=TextType.PLAIN_TEXT,
                        text="❌ キャンセル",
                        emoji=True,
                    ),
                    action_id=f"{ActionType.CANCEL.value}_{session_id}",
                    value=session_id,
                    style=ButtonStyle.DANGER,
                ),
            ]
        )
        blocks.append(actions.model_dump(exclude_none=True))
        
        return blocks

    def create_status_message(
        self,
        original_blocks: List[Dict[str, Any]],
        status: StatusType,
        message: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        ステータス更新メッセージを生成する
        
        Requirements: 5.1, 5.2, 5.3, 5.4
        
        Args:
            original_blocks: 元のメッセージブロック
            status: 更新後のステータス
            message: 追加メッセージ（オプション）
            
        Returns:
            更新されたBlock Kitブロックのリスト
        """
        # 元のブロックからアクションブロックを除去
        blocks = []
        for block in original_blocks:
            if block.get("type") != BlockType.ACTIONS.value:
                blocks.append(block)
        
        # ステータスに応じた絵文字とテキスト
        status_emoji_map = {
            StatusType.APPROVED: "✅",
            StatusType.REVISING: "✏️",
            StatusType.CANCELLED: "❌",
            StatusType.ERROR: "⚠️",
        }
        
        status_text_map = {
            StatusType.APPROVED: "承認済み",
            StatusType.REVISING: "修正中",
            StatusType.CANCELLED: "キャンセル済み",
            StatusType.ERROR: "エラー",
        }
        
        emoji = status_emoji_map.get(status, "ℹ️")
        status_text = status_text_map.get(status, "不明")
        
        # タイムスタンプを追加 (Requirement 5.4)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # コンテキストブロックを追加
        context_elements = [
            TextObject(
                type=TextType.MRKDWN,
                text=f"{emoji} *ステータス:* {status_text}",
            ),
            TextObject(
                type=TextType.MRKDWN,
                text=f"🕐 *更新日時:* {timestamp}",
            ),
        ]
        
        if message:
            context_elements.append(
                TextObject(
                    type=TextType.MRKDWN,
                    text=f"💬 {message}",
                )
            )
        
        context = ContextBlock(elements=context_elements)
        blocks.append(context.model_dump(exclude_none=True))
        
        return blocks

    def create_reminder_message(
        self,
        session_id: str,
        content_type: ContentType,
        original_message_link: str,
        reminder_count: int,
    ) -> List[Dict[str, Any]]:
        """
        リマインダーメッセージを生成する
        
        Requirements: 6.4
        
        Args:
            session_id: セッションID
            content_type: コンテンツタイプ
            original_message_link: 元のメッセージへのリンク
            reminder_count: リマインダー送信回数
            
        Returns:
            Block Kitブロックのリスト
        """
        blocks = []
        
        # ヘッダーブロック
        content_type_label = "議事録" if content_type == ContentType.MINUTES else "タスク"
        header = HeaderBlock(
            text=TextObject(
                type=TextType.PLAIN_TEXT,
                text=f"🔔 リマインダー: {content_type_label}の確認",
                emoji=True,
            )
        )
        blocks.append(header.model_dump(exclude_none=True))
        
        # メッセージセクション
        message_text = (
            f"まだ確認されていない{content_type_label}があります。\n"
            f"以下のリンクから確認をお願いします。\n\n"
            f"<{original_message_link}|元のメッセージを確認>"
        )
        
        message_section = SectionBlock(
            text=TextObject(
                type=TextType.MRKDWN,
                text=message_text,
            )
        )
        blocks.append(message_section.model_dump(exclude_none=True))
        
        # コンテキスト情報
        context = ContextBlock(
            elements=[
                TextObject(
                    type=TextType.MRKDWN,
                    text=f"📊 リマインダー送信回数: {reminder_count}/3",
                ),
            ]
        )
        blocks.append(context.model_dump(exclude_none=True))
        
        return blocks

    def create_feedback_modal(
        self,
        session_id: str,
        content_type: ContentType,
    ) -> Dict[str, Any]:
        """
        フィードバックモーダルを生成する
        
        Requirements: 4.1, 4.2, 4.3
        
        Args:
            session_id: セッションID
            content_type: コンテンツタイプ
            
        Returns:
            モーダルビューのJSON
        """
        content_type_label = "議事録" if content_type == ContentType.MINUTES else "タスク"
        
        # 入力ブロック (Requirement 4.1)
        input_block = InputBlock(
            block_id=f"feedback_input_{session_id}",
            label=TextObject(
                type=TextType.PLAIN_TEXT,
                text="修正内容",
                emoji=True,
            ),
            element=PlainTextInputElement(
                action_id=f"feedback_text_{session_id}",
                multiline=True,
                placeholder=TextObject(
                    type=TextType.PLAIN_TEXT,
                    text=f"{content_type_label}の修正内容を入力してください...",
                    emoji=True,
                ),
            ),
        )
        
        # モーダルビュー
        modal = {
            "type": "modal",
            "callback_id": f"feedback_modal_{session_id}",
            "title": TextObject(
                type=TextType.PLAIN_TEXT,
                text=f"{content_type_label}の修正",
                emoji=True,
            ).model_dump(exclude_none=True),
            "submit": TextObject(  # Requirement 4.2
                type=TextType.PLAIN_TEXT,
                text="送信",
                emoji=True,
            ).model_dump(exclude_none=True),
            "close": TextObject(  # Requirement 4.3
                type=TextType.PLAIN_TEXT,
                text="キャンセル",
                emoji=True,
            ).model_dump(exclude_none=True),
            "blocks": [
                input_block.model_dump(exclude_none=True),
            ],
        }
        
        return modal
