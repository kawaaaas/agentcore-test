"""
Slack Handler

Slack からのインタラクション（ボタンクリック等）を処理するコンポーネント。
署名検証、ペイロードパース、アクション処理を担当する。

Requirements: 3.1, 3.2, 3.3, 3.4, 4.4, 4.5, 4.6, 9.2, 9.3
"""

import hashlib
import hmac
import json
import time
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """アクションタイプ"""
    APPROVE = "approve"
    REVISE = "revise"
    CANCEL = "cancel"


class InteractionType(str, Enum):
    """インタラクションタイプ"""
    BLOCK_ACTIONS = "block_actions"
    VIEW_SUBMISSION = "view_submission"


class SlackHandler:
    """
    Slack インタラクションハンドラー
    
    Slack からのインタラクションイベントを処理する。
    署名検証、ペイロードパース、アクション処理を行う。
    """
    
    # タイムスタンプ検証の許容時間（秒）
    TIMESTAMP_TOLERANCE = 300  # 5分
    
    def __init__(self, signing_secret: str):
        """
        初期化
        
        Args:
            signing_secret: Slack Signing Secret
        """
        self.signing_secret = signing_secret
    
    def verify_signature(
        self,
        timestamp: str,
        body: str,
        signature: str,
    ) -> bool:
        """
        Slack リクエストの署名を検証する
        
        Requirements: 9.2, 9.3
        
        Args:
            timestamp: リクエストのタイムスタンプ（X-Slack-Request-Timestamp）
            body: リクエストボディ
            signature: Slack の署名（X-Slack-Signature）
            
        Returns:
            署名が有効な場合 True、無効な場合 False
        """
        # タイムスタンプ検証（5分以内）(Requirement 9.2)
        try:
            request_timestamp = int(timestamp)
            current_timestamp = int(time.time())
            
            if abs(current_timestamp - request_timestamp) > self.TIMESTAMP_TOLERANCE:
                return False
        except (ValueError, TypeError):
            return False
        
        # 署名検証（HMAC-SHA256）(Requirement 9.3)
        sig_basestring = f"v0:{timestamp}:{body}"
        
        my_signature = (
            "v0="
            + hmac.new(
                self.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )
        
        # タイミング攻撃を防ぐため、hmac.compare_digest を使用
        return hmac.compare_digest(my_signature, signature)
    
    def parse_interaction(self, payload: str) -> Dict[str, Any]:
        """
        インタラクションペイロードをパースする
        
        Requirements: 3.4
        
        Args:
            payload: JSON文字列のペイロード
            
        Returns:
            パースされたペイロード辞書
            
        Raises:
            ValueError: JSONパースに失敗した場合
        """
        try:
            return json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse interaction payload: {e}")
    
    def handle_block_action(self, payload: Dict[str, Any]) -> tuple[ActionType, str]:
        """
        ブロックアクションを処理する
        
        Requirements: 3.1, 3.2, 3.3
        
        Args:
            payload: パースされたインタラクションペイロード
            
        Returns:
            (ActionType, session_id) のタプル
            
        Raises:
            ValueError: アクションの解析に失敗した場合
        """
        try:
            # アクション情報を取得
            actions = payload.get("actions", [])
            if not actions:
                raise ValueError("No actions found in payload")
            
            action = actions[0]
            action_id = action.get("action_id", "")
            value = action.get("value", "")
            
            # action_id から ActionType を抽出
            # フォーマット: "{action_type}_{session_id}"
            if "_" not in action_id:
                raise ValueError(f"Invalid action_id format: {action_id}")
            
            action_type_str, session_id = action_id.split("_", 1)
            
            # ActionType に変換
            try:
                action_type = ActionType(action_type_str)
            except ValueError:
                raise ValueError(f"Unknown action type: {action_type_str}")
            
            return action_type, session_id
            
        except (KeyError, IndexError) as e:
            raise ValueError(f"Failed to parse block action: {e}")
    
    def handle_view_submission(self, payload: Dict[str, Any]) -> tuple[str, str]:
        """
        ビュー送信（モーダル送信）を処理する
        
        Requirements: 4.4, 4.5, 4.6
        
        Args:
            payload: パースされたビュー送信ペイロード
            
        Returns:
            (session_id, feedback_text) のタプル
            
        Raises:
            ValueError: 修正内容が空の場合、または解析に失敗した場合
        """
        try:
            # ビュー情報を取得
            view = payload.get("view", {})
            callback_id = view.get("callback_id", "")
            
            # callback_id から session_id を抽出
            # フォーマット: "feedback_modal_{session_id}"
            if not callback_id.startswith("feedback_modal_"):
                raise ValueError(f"Invalid callback_id format: {callback_id}")
            
            session_id = callback_id.replace("feedback_modal_", "")
            
            # 入力値を取得
            state_values = view.get("state", {}).get("values", {})
            
            # feedback_input_{session_id} ブロックから値を取得
            input_block_id = f"feedback_input_{session_id}"
            action_id = f"feedback_text_{session_id}"
            
            if input_block_id not in state_values:
                raise ValueError(f"Input block not found: {input_block_id}")
            
            input_value = (
                state_values[input_block_id]
                .get(action_id, {})
                .get("value", "")
            )
            
            # 空入力のチェック (Requirement 4.5)
            feedback_text = input_value.strip()
            if not feedback_text:
                raise ValueError("Feedback text cannot be empty")
            
            return session_id, feedback_text
            
        except (KeyError, IndexError) as e:
            raise ValueError(f"Failed to parse view submission: {e}")
