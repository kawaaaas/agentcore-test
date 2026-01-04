"""
Slack承認フロー管理

議事録の承認フローをSlack Block Kitで実装する。
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import boto3
from bedrock_agentcore.memory import MemoryClient

from agents.models.approval import ApprovalStatus, PendingMinutesBlob, PendingMinutesRecord
from agents.models.minutes import Minutes


class ApprovalFlow:
    """
    Slack承認フロー管理クラス
    
    議事録の承認・修正フローをSlack Block Kitで実装する。
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    
    # Slackメッセージの文字数制限
    SLACK_MESSAGE_LIMIT = 4000
    # 省略時のプレビュー文字数
    PREVIEW_LENGTH = 3000
    
    def __init__(
        self,
        slack_client: Optional[Any] = None,
        memory_client: Optional[MemoryClient] = None,
        dynamodb_table_name: Optional[str] = None,
    ):
        """
        初期化
        
        Args:
            slack_client: Slack APIクライアント（オプション）
            memory_client: AgentCore Memoryクライアント（オプション）
            dynamodb_table_name: DynamoDBテーブル名（オプション、環境変数から取得）
        """
        self.slack_client = slack_client
        self.memory_client = memory_client
        self.dynamodb_table_name = dynamodb_table_name or os.environ.get("DYNAMODB_TABLE_NAME")
        
        # DynamoDBクライアントの初期化
        if self.dynamodb_table_name:
            self.dynamodb = boto3.resource("dynamodb")
            self.table = self.dynamodb.Table(self.dynamodb_table_name)
        else:
            self.dynamodb = None
            self.table = None
    
    def create_approval_message(
        self,
        minutes: Minutes,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        承認メッセージを生成する
        
        Slack Block Kitを使用して、議事録の承認/修正ボタンを含むメッセージを生成する。
        メッセージが4000文字を超える場合は省略処理を行う。
        
        Requirements: 4.1, 4.2
        
        Args:
            minutes: 議事録オブジェクト
            session_id: AgentCoreセッションID
        
        Returns:
            Slack Block Kit形式のメッセージ辞書
        """
        # 議事録をMarkdown形式に変換
        from agents.tools.formatter import MinutesFormatter
        
        formatter = MinutesFormatter()
        markdown_content = formatter.to_markdown(minutes)
        
        # 文字数制限を考慮した省略処理
        if len(markdown_content) > self.PREVIEW_LENGTH:
            markdown_content = markdown_content[:self.PREVIEW_LENGTH] + "\n\n...(省略されました)"
        
        # Block Kit メッセージを構築
        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📝 議事録が生成されました",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{minutes.title}*\n{minutes.date.strftime('%Y年%m月%d日 %H:%M')}",
                },
            },
            {
                "type": "divider",
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": markdown_content,
                },
            },
            {
                "type": "divider",
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "この議事録を承認しますか？修正が必要な場合は「修正」ボタンをクリックしてください。",
                },
            },
            {
                "type": "actions",
                "block_id": f"approval_actions_{session_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ 承認",
                            "emoji": True,
                        },
                        "style": "primary",
                        "value": session_id,
                        "action_id": "approve_minutes",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✏️ 修正",
                            "emoji": True,
                        },
                        "style": "danger",
                        "value": session_id,
                        "action_id": "request_revision",
                    },
                ],
            },
        ]
        
        return {
            "blocks": blocks,
            "text": f"議事録が生成されました: {minutes.title}",
        }
    
    def create_revision_modal(
        self,
        session_id: str,
        minutes: Minutes,
    ) -> Dict[str, Any]:
        """
        修正入力フォームを生成する
        
        Slack Modalを使用して、議事録の修正内容を入力するフォームを生成する。
        
        Requirements: 4.4
        
        Args:
            session_id: AgentCoreセッションID
            minutes: 現在の議事録オブジェクト
        
        Returns:
            Slack Modal形式の辞書
        """
        return {
            "type": "modal",
            "callback_id": f"revision_modal_{session_id}",
            "title": {
                "type": "plain_text",
                "text": "議事録の修正",
                "emoji": True,
            },
            "submit": {
                "type": "plain_text",
                "text": "修正を送信",
                "emoji": True,
            },
            "close": {
                "type": "plain_text",
                "text": "キャンセル",
                "emoji": True,
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{minutes.title}*\nの修正内容を入力してください。",
                    },
                },
                {
                    "type": "input",
                    "block_id": "revision_instructions",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "revision_text",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "例: 参加者に田中さんを追加してください。\n決定事項に予算承認を追加してください。",
                        },
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "修正指示",
                        "emoji": True,
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "💡 具体的な修正内容を記述してください。AIが修正を反映した議事録を再生成します。",
                        },
                    ],
                },
            ],
            "private_metadata": json.dumps({
                "session_id": session_id,
            }),
        }
    
    def handle_action(
        self,
        action_id: str,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        承認/修正アクションを処理する
        
        ユーザーのアクション（承認/修正）に応じて状態遷移を行う。
        PENDING → APPROVED または PENDING → REVISION_REQUESTED
        
        Requirements: 4.3, 4.4, 4.5
        
        Args:
            action_id: アクションID（"approve_minutes" または "request_revision"）
            session_id: AgentCoreセッションID
            user_id: Slackユーザーid（オプション）
        
        Returns:
            処理結果を含む辞書
            {
                "status": ApprovalStatus,
                "message": str,
                "updated_at": datetime,
            }
        """
        current_time = datetime.now()
        
        if action_id == "approve_minutes":
            # 承認アクション
            return {
                "status": ApprovalStatus.APPROVED,
                "message": "✅ 議事録が承認されました。S3に保存します。",
                "updated_at": current_time,
                "user_id": user_id,
            }
        
        elif action_id == "request_revision":
            # 修正リクエストアクション
            return {
                "status": ApprovalStatus.REVISION_REQUESTED,
                "message": "✏️ 修正内容を入力してください。",
                "updated_at": current_time,
                "user_id": user_id,
            }
        
        else:
            # 不明なアクション
            raise ValueError(f"Unknown action_id: {action_id}")
    
    def save_pending_minutes(
        self,
        session_id: str,
        minutes: Minutes,
        source_transcript: str,
        slack_channel_id: Optional[str] = None,
        slack_message_ts: Optional[str] = None,
    ) -> str:
        """
        承認待ち議事録を永続化する
        
        議事録本体をAgentCore Memory STMに保存し、メタデータをDynamoDBに保存する。
        
        Requirements: 4.3, 7.5
        
        Args:
            session_id: AgentCoreセッションID
            minutes: 議事録オブジェクト
            source_transcript: 元の書き起こしテキスト
            slack_channel_id: SlackチャンネルID（オプション）
            slack_message_ts: Slackメッセージタイムスタンプ（オプション）
        
        Returns:
            Memory blob ID
        
        Raises:
            ValueError: Memory clientまたはDynamoDBテーブルが初期化されていない場合
            Exception: 保存処理に失敗した場合
        """
        if not self.memory_client:
            raise ValueError("Memory client is not initialized")
        
        if not self.table:
            raise ValueError("DynamoDB table is not initialized")
        
        try:
            # 議事録をJSONにシリアライズ
            minutes_json = minutes.model_dump_json()
            
            # PendingMinutesBlobを作成
            blob = PendingMinutesBlob(
                session_id=session_id,
                minutes_json=minutes_json,
                source_transcript=source_transcript,
                revision_history=[],
            )
            
            # AgentCore Memoryに保存
            blob_content = blob.model_dump_json()
            memory_response = self.memory_client.create_blob_event(
                session_id=session_id,
                content=blob_content,
            )
            
            # Blob IDを取得
            blob_id = memory_response.get("eventId")
            if not blob_id:
                raise ValueError("Failed to get blob_id from Memory response")
            
            # 現在時刻と有効期限を設定
            current_time = datetime.now()
            expires_at = current_time + timedelta(hours=24)
            
            # DynamoDBにメタデータを保存
            record = PendingMinutesRecord(
                session_id=session_id,
                status=ApprovalStatus.PENDING,
                created_at=current_time,
                updated_at=current_time,
                slack_message_ts=slack_message_ts,
                slack_channel_id=slack_channel_id,
                memory_blob_id=blob_id,
                revision_count=0,
                expires_at=expires_at,
            )
            
            # DynamoDBに保存（Pydanticモデルを辞書に変換）
            item = record.model_dump()
            # datetimeをISO形式文字列に変換
            item["created_at"] = item["created_at"].isoformat()
            item["updated_at"] = item["updated_at"].isoformat()
            item["expires_at"] = item["expires_at"].isoformat()
            item["status"] = item["status"].value
            
            self.table.put_item(Item=item)
            
            return blob_id
            
        except Exception as e:
            raise Exception(f"Failed to save pending minutes: {str(e)}") from e
    
    def get_pending_minutes(
        self,
        session_id: str,
    ) -> Tuple[PendingMinutesRecord, Minutes]:
        """
        承認待ち議事録を取得する
        
        DynamoDBからメタデータを取得し、AgentCore Memoryから議事録本体を取得する。
        
        Requirements: 4.3, 4.4
        
        Args:
            session_id: AgentCoreセッションID
        
        Returns:
            (PendingMinutesRecord, Minutes)のタプル
        
        Raises:
            ValueError: Memory clientまたはDynamoDBテーブルが初期化されていない場合
            KeyError: 指定されたsession_idのレコードが見つからない場合
            Exception: 取得処理に失敗した場合
        """
        if not self.memory_client:
            raise ValueError("Memory client is not initialized")
        
        if not self.table:
            raise ValueError("DynamoDB table is not initialized")
        
        try:
            # DynamoDBからメタデータを取得
            response = self.table.get_item(Key={"session_id": session_id})
            
            if "Item" not in response:
                raise KeyError(f"No pending minutes found for session_id: {session_id}")
            
            item = response["Item"]
            
            # PendingMinutesRecordに変換
            # datetime文字列をdatetimeオブジェクトに変換
            item["created_at"] = datetime.fromisoformat(item["created_at"])
            item["updated_at"] = datetime.fromisoformat(item["updated_at"])
            item["expires_at"] = datetime.fromisoformat(item["expires_at"])
            item["status"] = ApprovalStatus(item["status"])
            
            record = PendingMinutesRecord(**item)
            
            # AgentCore Memoryから議事録本体を取得
            # Note: MemoryClientのAPIは実装依存のため、適切なメソッドを使用
            # ここではget_event()を想定
            memory_response = self.memory_client.get_event(
                session_id=session_id,
                event_id=record.memory_blob_id,
            )
            
            # Blobコンテンツを取得
            blob_content = memory_response.get("content")
            if not blob_content:
                raise ValueError("Failed to get blob content from Memory")
            
            # PendingMinutesBlobに変換
            blob = PendingMinutesBlob.model_validate_json(blob_content)
            
            # MinutesオブジェクトをJSONから復元
            minutes = Minutes.model_validate_json(blob.minutes_json)
            
            return record, minutes
            
        except KeyError:
            raise
        except Exception as e:
            raise Exception(f"Failed to get pending minutes: {str(e)}") from e

