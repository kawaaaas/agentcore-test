"""
タスク永続化

承認待ちタスクリストをAgentCore Memory STMとDynamoDBに永続化する。
Requirements: 8.1, 8.2, 8.3, 8.5
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import boto3
from bedrock_agentcore.memory import MemoryClient

from agents.tools.task_models import TaskList
from agents.utils.retry import with_retry

# ロガー設定
logger = logging.getLogger(__name__)


class Task_Persistence:
    """
    タスク永続化クラス
    
    承認待ちタスクリストをAgentCore Memory STMとDynamoDBに永続化し、
    session_idをキーに復元する機能を提供する。
    
    Requirements: 8.1, 8.2, 8.3, 8.5
    """
    
    def __init__(
        self,
        memory_client: Optional[MemoryClient] = None,
        dynamodb_table_name: Optional[str] = None,
    ):
        """
        初期化
        
        Args:
            memory_client: AgentCore Memoryクライアント（オプション）
            dynamodb_table_name: DynamoDBテーブル名（オプション、環境変数から取得）
        """
        self.memory_client = memory_client
        self.dynamodb_table_name = dynamodb_table_name or os.environ.get(
            "DYNAMODB_SESSION_TABLE_NAME"
        )
        
        # DynamoDBクライアントの初期化
        if self.dynamodb_table_name:
            self.dynamodb = boto3.resource("dynamodb")
            self.table = self.dynamodb.Table(self.dynamodb_table_name)
        else:
            self.dynamodb = None
            self.table = None
    
    @with_retry(
        max_retries=3,
        base_delay=1.0,
        exceptions=(Exception,),
    )
    def save_pending_tasks(
        self,
        session_id: str,
        task_list: TaskList,
        slack_channel_id: Optional[str] = None,
        slack_message_ts: Optional[str] = None,
    ) -> str:
        """
        承認待ちタスクリストを永続化する
        
        タスクリスト本体をAgentCore Memory STMに保存し、
        承認状態・メタデータをDynamoDB Session_Tableに保存する。
        
        Requirements: 8.1, 8.2, 8.3, 8.5, 7.1, 7.3
        
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
        
        logger.info(f"承認待ちタスクリストを保存開始: session_id={session_id}")
        
        # タスクリストをJSONにシリアライズ
        task_list_json = task_list.model_dump_json()
        
        # AgentCore Memory STMに保存
        # STMは会話イベントの保持に使用され、デフォルトで90日間保持される
        memory_response = self.memory_client.create_blob_event(
            session_id=session_id,
            content=task_list_json,
        )
        
        # Blob IDを取得
        blob_id = memory_response.get("eventId")
        if not blob_id:
            raise ValueError("Failed to get blob_id from Memory response")
        
        logger.info(f"Memory STMに保存完了: blob_id={blob_id}")
        
        # 現在時刻と有効期限を設定（24時間後）
        current_time = datetime.now()
        expires_at = current_time + timedelta(hours=24)
        
        # DynamoDB Session_Tableにメタデータを保存
        # 高速なステータス検索のため
        item = {
            "session_id": session_id,
            "status": task_list.status.value,
            "minutes_id": task_list.minutes_id,
            "task_count": len(task_list.tasks),
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat(),
            "expires_at": expires_at.isoformat(),
            "memory_blob_id": blob_id,
        }
        
        # オプションフィールドを追加
        if slack_channel_id:
            item["slack_channel_id"] = slack_channel_id
        if slack_message_ts:
            item["slack_message_ts"] = slack_message_ts
        
        self.table.put_item(Item=item)
        
        logger.info(f"DynamoDBに保存完了: session_id={session_id}")
        
        return blob_id
    
    @with_retry(
        max_retries=3,
        base_delay=1.0,
        exceptions=(Exception,),
    )
    def load_pending_tasks(
        self,
        session_id: str,
    ) -> TaskList:
        """
        承認待ちタスクリストを復元する
        
        DynamoDBからメタデータを取得し、AgentCore Memory STMから
        タスクリスト本体を取得する。
        
        Requirements: 8.1, 8.2, 8.3, 7.1, 7.3
        
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
        
        logger.info(f"承認待ちタスクリストを復元開始: session_id={session_id}")
        
        # DynamoDBからメタデータを取得
        response = self.table.get_item(Key={"session_id": session_id})
        
        if "Item" not in response:
            raise KeyError(f"No pending tasks found for session_id: {session_id}")
        
        item = response["Item"]
        
        # Memory blob IDを取得
        memory_blob_id = item.get("memory_blob_id")
        if not memory_blob_id:
            raise ValueError("memory_blob_id not found in DynamoDB item")
        
        logger.info(f"DynamoDBからメタデータ取得完了: blob_id={memory_blob_id}")
        
        # AgentCore Memory STMからタスクリスト本体を取得
        memory_response = self.memory_client.get_event(
            session_id=session_id,
            event_id=memory_blob_id,
        )
        
        # Blobコンテンツを取得
        blob_content = memory_response.get("content")
        if not blob_content:
            raise ValueError("Failed to get blob content from Memory")
        
        logger.info(f"Memory STMからタスクリスト取得完了")
        
        # TaskListオブジェクトをJSONから復元
        task_list = TaskList.model_validate_json(blob_content)
        
        logger.info(f"タスクリスト復元完了: {len(task_list.tasks)}個のタスク")
        
        return task_list
