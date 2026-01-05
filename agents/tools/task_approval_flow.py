"""
タスク承認フロー管理

タスクの承認フローをSlack Block Kitで実装する。
Requirements: 5.2, 5.3, 5.4, 5.5, 5.6
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import boto3
from bedrock_agentcore.memory import MemoryClient

from agents.tools.task_formatter import Task_Formatter
from agents.tools.task_models import Task, TaskList, TaskListStatus


class TaskApprovalFlow:
    """
    タスク承認フロー管理クラス
    
    タスクの承認・修正フローをSlack Block Kitで実装する。
    Requirements: 5.2, 5.3, 5.4, 5.5, 5.6
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
    
    def create_task_approval_message(
        self,
        task_list: TaskList,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        タスク承認メッセージを生成する
        
        Slack Block Kitを使用して、タスク一覧プレビュー、承認/修正/キャンセルボタン、
        個別削除ボタンを含むメッセージを生成する。
        
        確認フロー中の会話をSTMに保存する。
        
        Requirements: 5.2, 9.5
        
        Args:
            task_list: タスクリストオブジェクト
            session_id: AgentCoreセッションID
        
        Returns:
            Slack Block Kit形式のメッセージ辞書
        """
        # タスクをMarkdown形式に変換
        formatter = Task_Formatter()
        markdown_content = formatter.to_markdown(task_list)
        
        # 文字数制限を考慮した省略処理
        if len(markdown_content) > self.PREVIEW_LENGTH:
            markdown_content = markdown_content[:self.PREVIEW_LENGTH] + "\n\n...(省略されました)"
        
        # Requirement 9.5: 確認フロー中の会話をSTMに保存（アシスタントからのメッセージ）
        self.save_conversation_to_stm(
            session_id=session_id,
            actor_id="assistant",
            role="assistant",
            message=f"タスクを抽出しました。{len(task_list.tasks)}件のタスクが見つかりました。",
        )
        
        # Block Kit メッセージを構築
        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📋 タスクが抽出されました",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*議事録からタスクを抽出しました*\n抽出されたタスク数: {len(task_list.tasks)}件",
                },
            },
            {
                "type": "divider",
            },
        ]
        
        # タスク一覧プレビュー（Requirement 5.2）
        if task_list.tasks:
            # 優先度でソート
            sorted_tasks = sorted(
                task_list.tasks,
                key=lambda t: Task_Formatter.PRIORITY_ORDER[t.priority]
            )
            
            # 各タスクをセクションとして追加（個別削除ボタン付き）
            for task in sorted_tasks:
                # タスク情報
                task_text = f"*{task.title}*\n"
                task_text += f"優先度: {task.priority.value.upper()}"
                
                if task.assignee:
                    task_text += f" | 担当: {task.assignee}"
                if task.due_date:
                    task_text += f" | 期限: {task.due_date.strftime('%Y-%m-%d')}"
                
                task_text += f"\n{task.description[:100]}..."
                
                # タスクセクション
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": task_text,
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🗑️ 削除",
                            "emoji": True,
                        },
                        "style": "danger",
                        "value": task.id,
                        "action_id": f"delete_task_{task.id}",
                    },
                })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_タスクが見つかりませんでした_",
                },
            })
        
        blocks.append({
            "type": "divider",
        })
        
        # 承認/修正/キャンセルボタン（Requirements 5.2）
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "このタスクリストを承認しますか？修正が必要な場合は「修正」ボタンをクリックしてください。",
                },
            },
            {
                "type": "actions",
                "block_id": f"task_approval_actions_{session_id}",
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
                        "action_id": "approve_tasks",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✏️ 修正",
                            "emoji": True,
                        },
                        "value": session_id,
                        "action_id": "request_task_revision",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ キャンセル",
                            "emoji": True,
                        },
                        "style": "danger",
                        "value": session_id,
                        "action_id": "cancel_tasks",
                    },
                ],
            },
        ])
        
        return {
            "blocks": blocks,
            "text": f"タスクが抽出されました: {len(task_list.tasks)}件",
        }
    
    def create_task_revision_modal(
        self,
        session_id: str,
        task_list: TaskList,
    ) -> Dict[str, Any]:
        """
        タスク修正入力フォームを生成する
        
        Slack Modalを使用して、タスクの修正内容を入力するフォームを生成する。
        
        Requirements: 5.4
        
        Args:
            session_id: AgentCoreセッションID
            task_list: 現在のタスクリストオブジェクト
        
        Returns:
            Slack Modal形式の辞書
        """
        return {
            "type": "modal",
            "callback_id": f"task_revision_modal_{session_id}",
            "title": {
                "type": "plain_text",
                "text": "タスクの修正",
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
                        "text": f"*タスクリスト（{len(task_list.tasks)}件）*\nの修正内容を入力してください。",
                    },
                },
                {
                    "type": "input",
                    "block_id": "task_revision_instructions",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "task_revision_text",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "例: タスク「〇〇」の担当者を田中さんに変更してください。\n新しいタスク「△△」を追加してください。",
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
                            "text": "💡 具体的な修正内容を記述してください。AIが修正を反映したタスクリストを再生成します。",
                        },
                    ],
                },
            ],
            "private_metadata": json.dumps({
                "session_id": session_id,
            }),
        }
    
    def create_add_task_modal(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        タスク追加フォームを生成する
        
        Slack Modalを使用して、新しいタスクを追加するフォームを生成する。
        
        Requirements: 5.6
        
        Args:
            session_id: AgentCoreセッションID
        
        Returns:
            Slack Modal形式の辞書
        """
        return {
            "type": "modal",
            "callback_id": f"add_task_modal_{session_id}",
            "title": {
                "type": "plain_text",
                "text": "タスクの追加",
                "emoji": True,
            },
            "submit": {
                "type": "plain_text",
                "text": "追加",
                "emoji": True,
            },
            "close": {
                "type": "plain_text",
                "text": "キャンセル",
                "emoji": True,
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "task_title",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "タスクのタイトルを入力",
                        },
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "タイトル",
                        "emoji": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "task_description",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "description_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "タスクの詳細を入力",
                        },
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "説明",
                        "emoji": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "task_assignee",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "assignee_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "担当者名（オプション）",
                        },
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "担当者",
                        "emoji": True,
                    },
                    "optional": True,
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
        承認/修正/キャンセルアクションを処理する
        
        ユーザーのアクション（承認/修正/キャンセル）に応じて状態遷移を行う。
        - approve → APPROVED
        - request_revision → REVISION_REQUESTED
        - cancel → CANCELLED
        
        確認フロー中の会話をSTMに保存する。
        
        Requirements: 5.3, 5.4, 9.5
        
        Args:
            action_id: アクションID（"approve_tasks", "request_task_revision", "cancel_tasks"）
            session_id: AgentCoreセッションID
            user_id: Slackユーザーid（オプション）
        
        Returns:
            処理結果を含む辞書
            {
                "status": TaskListStatus,
                "message": str,
                "updated_at": datetime,
            }
        """
        current_time = datetime.now()
        
        if action_id == "approve_tasks":
            # 承認アクション → APPROVED
            message = "✅ タスクリストが承認されました。GitHub Issuesへの登録を準備します。"
            
            # Requirement 9.5: 確認フロー中の会話をSTMに保存
            if user_id:
                self.save_conversation_to_stm(
                    session_id=session_id,
                    actor_id=user_id,
                    role="user",
                    message="タスクリストを承認しました",
                )
            
            return {
                "status": TaskListStatus.APPROVED,
                "message": message,
                "updated_at": current_time,
                "user_id": user_id,
            }
        
        elif action_id == "request_task_revision":
            # 修正リクエストアクション → REVISION_REQUESTED
            message = "✏️ 修正内容を入力してください。"
            
            # Requirement 9.5: 確認フロー中の会話をSTMに保存
            if user_id:
                self.save_conversation_to_stm(
                    session_id=session_id,
                    actor_id=user_id,
                    role="user",
                    message="タスクリストの修正をリクエストしました",
                )
            
            return {
                "status": TaskListStatus.REVISION_REQUESTED,
                "message": message,
                "updated_at": current_time,
                "user_id": user_id,
            }
        
        elif action_id == "cancel_tasks":
            # キャンセルアクション → CANCELLED
            message = "❌ タスクリストがキャンセルされました。"
            
            # Requirement 9.5: 確認フロー中の会話をSTMに保存
            if user_id:
                self.save_conversation_to_stm(
                    session_id=session_id,
                    actor_id=user_id,
                    role="user",
                    message="タスクリストをキャンセルしました",
                )
            
            return {
                "status": TaskListStatus.CANCELLED,
                "message": message,
                "updated_at": current_time,
                "user_id": user_id,
            }
        
        else:
            # 不明なアクション
            raise ValueError(f"Unknown action_id: {action_id}")
    
    def delete_task(
        self,
        task_list: TaskList,
        task_id: str,
        user_id: Optional[str] = None,
    ) -> TaskList:
        """
        タスクリストから指定されたタスクを削除する
        
        確認フロー中の会話をSTMに保存する。
        
        Requirements: 5.5, 9.5
        
        Args:
            task_list: タスクリストオブジェクト
            task_id: 削除するタスクのID
            user_id: Slackユーザーid（オプション）
        
        Returns:
            更新されたタスクリストオブジェクト
        
        Raises:
            ValueError: 指定されたタスクIDが見つからない場合
        """
        # タスクIDで検索
        task_to_delete = None
        for task in task_list.tasks:
            if task.id == task_id:
                task_to_delete = task
                break
        
        if not task_to_delete:
            raise ValueError(f"Task with id {task_id} not found")
        
        # Requirement 9.5: 確認フロー中の会話をSTMに保存
        if user_id:
            self.save_conversation_to_stm(
                session_id=task_list.session_id,
                actor_id=user_id,
                role="user",
                message=f"タスク「{task_to_delete.title}」を削除しました",
            )
        
        # タスクを削除
        updated_tasks = [t for t in task_list.tasks if t.id != task_id]
        
        # 新しいTaskListを作成
        updated_task_list = TaskList(
            session_id=task_list.session_id,
            minutes_id=task_list.minutes_id,
            tasks=updated_tasks,
            status=task_list.status,
            created_at=task_list.created_at,
            updated_at=datetime.now(),
        )
        
        return updated_task_list
    
    def add_task(
        self,
        task_list: TaskList,
        task: Task,
        user_id: Optional[str] = None,
    ) -> TaskList:
        """
        タスクリストに新しいタスクを追加する
        
        確認フロー中の会話をSTMに保存する。
        
        Requirements: 5.6, 9.5
        
        Args:
            task_list: タスクリストオブジェクト
            task: 追加するタスクオブジェクト
            user_id: Slackユーザーid（オプション）
        
        Returns:
            更新されたタスクリストオブジェクト
        """
        # Requirement 9.5: 確認フロー中の会話をSTMに保存
        if user_id:
            self.save_conversation_to_stm(
                session_id=task_list.session_id,
                actor_id=user_id,
                role="user",
                message=f"タスク「{task.title}」を追加しました",
            )
        
        # タスクを追加
        updated_tasks = task_list.tasks + [task]
        
        # 新しいTaskListを作成
        updated_task_list = TaskList(
            session_id=task_list.session_id,
            minutes_id=task_list.minutes_id,
            tasks=updated_tasks,
            status=task_list.status,
            created_at=task_list.created_at,
            updated_at=datetime.now(),
        )
        
        return updated_task_list
    
    def save_modification_pattern_to_ltm(
        self,
        session_id: str,
        actor_id: str,
        original_task: Task,
        modified_task: Task,
        modification_type: str,
    ) -> Optional[str]:
        """
        タスク修正パターンをLTMに保存する
        
        ユーザーがタスクを修正した際に、その修正内容をLTMに保存して学習する。
        
        Requirements: 9.1, 9.4
        
        Args:
            session_id: AgentCoreセッションID
            actor_id: ユーザーID（修正者）
            original_task: 修正前のタスク
            modified_task: 修正後のタスク
            modification_type: 修正タイプ（"title_change", "assignee_change", "priority_change", "due_date_change", "description_change"）
        
        Returns:
            Memory ID（成功時）、None（失敗時）
        """
        if not self.memory_client:
            return None
        
        try:
            # 修正パターンをJSON形式で構造化
            modification_pattern = {
                "modification_type": modification_type,
                "original": {
                    "title": original_task.title,
                    "description": original_task.description,
                    "assignee": original_task.assignee,
                    "due_date": original_task.due_date.isoformat() if original_task.due_date else None,
                    "priority": original_task.priority.value,
                },
                "modified": {
                    "title": modified_task.title,
                    "description": modified_task.description,
                    "assignee": modified_task.assignee,
                    "due_date": modified_task.due_date.isoformat() if modified_task.due_date else None,
                    "priority": modified_task.priority.value,
                },
                "actor_id": actor_id,
                "timestamp": datetime.now().isoformat(),
            }
            
            # LTMに保存（セマンティック検索用）
            # ナレッジとして保存し、類似パターンの検索を可能にする
            content = json.dumps(modification_pattern, ensure_ascii=False)
            
            response = self.memory_client.create_semantic_memory(
                session_id=session_id,
                content=content,
                namespace=f"task_modifications/{actor_id}",
            )
            
            memory_id = response.get("memoryId")
            return memory_id
            
        except Exception as e:
            # エラーが発生してもフローを止めない
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"LTMへの修正パターン保存に失敗: {e}")
            return None
    
    def handle_revision_submission(
        self,
        session_id: str,
        user_id: str,
        revision_instructions: str,
    ) -> None:
        """
        修正指示の送信を処理する
        
        ユーザーからの修正指示をSTMに保存する。
        
        Requirements: 9.5
        
        Args:
            session_id: AgentCoreセッションID
            user_id: ユーザーID
            revision_instructions: 修正指示内容
        """
        # Requirement 9.5: 確認フロー中の会話をSTMに保存
        self.save_conversation_to_stm(
            session_id=session_id,
            actor_id=user_id,
            role="user",
            message=f"修正指示: {revision_instructions}",
        )
    
    def save_conversation_to_stm(
        self,
        session_id: str,
        actor_id: str,
        role: str,
        message: str,
    ) -> Optional[str]:
        """
        確認フロー中の会話をSTMに保存する
        
        Requirements: 9.5
        
        Args:
            session_id: AgentCoreセッションID
            actor_id: ユーザーID
            role: ロール（"user" または "assistant"）
            message: メッセージ内容
        
        Returns:
            Event ID（成功時）、None（失敗時）
        """
        if not self.memory_client:
            return None
        
        try:
            # STMに会話イベントを保存
            response = self.memory_client.create_event(
                session_id=session_id,
                actor_id=actor_id,
                role=role,
                content=message,
            )
            
            event_id = response.get("eventId")
            return event_id
            
        except Exception as e:
            # エラーが発生してもフローを止めない
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"STMへの会話保存に失敗: {e}")
            return None
    
    def save_pending_tasks(
        self,
        session_id: str,
        task_list: TaskList,
        slack_channel_id: Optional[str] = None,
        slack_message_ts: Optional[str] = None,
    ) -> str:
        """
        承認待ちタスクリストを永続化する
        
        タスクリスト本体をAgentCore Memory STMに保存し、メタデータをDynamoDBに保存する。
        
        Requirements: 8.1, 8.2, 8.3, 8.5
        
        Args:
            session_id: AgentCoreセッションID
            task_list: タスクリストオブジェクト
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
            # タスクリストをJSONにシリアライズ
            task_list_json = task_list.model_dump_json()
            
            # AgentCore Memoryに保存
            memory_response = self.memory_client.create_blob_event(
                session_id=session_id,
                content=task_list_json,
            )
            
            # Blob IDを取得
            blob_id = memory_response.get("eventId")
            if not blob_id:
                raise ValueError("Failed to get blob_id from Memory response")
            
            # 現在時刻と有効期限を設定
            current_time = datetime.now()
            expires_at = current_time + timedelta(hours=24)
            
            # DynamoDBにメタデータを保存
            item = {
                "session_id": session_id,
                "status": task_list.status.value,
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat(),
                "slack_message_ts": slack_message_ts,
                "slack_channel_id": slack_channel_id,
                "memory_blob_id": blob_id,
                "expires_at": expires_at.isoformat(),
                "task_count": len(task_list.tasks),
            }
            
            self.table.put_item(Item=item)
            
            return blob_id
            
        except Exception as e:
            raise Exception(f"Failed to save pending tasks: {str(e)}") from e
    
    def get_pending_tasks(
        self,
        session_id: str,
    ) -> TaskList:
        """
        承認待ちタスクリストを取得する
        
        DynamoDBからメタデータを取得し、AgentCore Memoryからタスクリスト本体を取得する。
        
        Requirements: 8.1, 8.2, 8.3
        
        Args:
            session_id: AgentCoreセッションID
        
        Returns:
            タスクリストオブジェクト
        
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
                raise KeyError(f"No pending tasks found for session_id: {session_id}")
            
            item = response["Item"]
            
            # AgentCore Memoryからタスクリスト本体を取得
            memory_response = self.memory_client.get_event(
                session_id=session_id,
                event_id=item["memory_blob_id"],
            )
            
            # Blobコンテンツを取得
            blob_content = memory_response.get("content")
            if not blob_content:
                raise ValueError("Failed to get blob content from Memory")
            
            # TaskListオブジェクトをJSONから復元
            task_list = TaskList.model_validate_json(blob_content)
            
            return task_list
            
        except KeyError:
            raise
        except Exception as e:
            raise Exception(f"Failed to get pending tasks: {str(e)}") from e
