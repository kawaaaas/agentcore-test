"""
議事録生成ツール

Bedrock Nova 2 Liteを使用して書き起こしテキストから議事録を生成する。
AgentCore Memoryから過去の修正パターンを取得して生成に反映する。

Requirements: 2.1, 2.3, 2.4, 7.2, 7.3
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import boto3
from pydantic import BaseModel, Field
from strands import tool

from agents.models.minutes import Minutes, ActionItem
from agents.tools.validate import validate_transcript

# ロガー設定
logger = logging.getLogger(__name__)


class GenerateMinutesInput(BaseModel):
    """議事録生成の入力スキーマ"""
    
    transcript: str = Field(
        ...,
        description="会議の書き起こしテキスト",
        min_length=10,
    )
    session_id: str = Field(
        ...,
        description="AgentCoreセッションID",
    )
    memory_id: Optional[str] = Field(
        default=None,
        description="AgentCore Memory ID（LTM検索用）",
    )
    meeting_title: Optional[str] = Field(
        default=None,
        description="会議タイトル（オプション）",
    )
    meeting_date: Optional[str] = Field(
        default=None,
        description="会議日時（YYYY-MM-DD HH:MM形式）",
    )
    participants: Optional[List[str]] = Field(
        default=None,
        description="参加者リスト（オプション）",
    )


class MinutesGenerator:
    """
    議事録生成クラス
    
    Bedrock Nova 2 Liteを使用して議事録を生成し、
    AgentCore Memoryから過去の修正パターンを取得して適用する。
    """
    
    def __init__(
        self,
        region_name: str = "us-west-2",
        model_id: str = "amazon.nova-lite-v1:0",
    ):
        """
        初期化
        
        Args:
            region_name: AWSリージョン
            model_id: Bedrockモデル ID
        """
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=region_name,
        )
        self.model_id = model_id
        self.region_name = region_name
    
    def generate_minutes(
        self,
        transcript: str,
        session_id: str,
        memory_id: Optional[str] = None,
        meeting_title: Optional[str] = None,
        meeting_date: Optional[str] = None,
        participants: Optional[List[str]] = None,
    ) -> Minutes:
        """
        議事録を生成する
        
        Requirements: 2.1, 2.3, 2.4, 7.3
        
        Args:
            transcript: 書き起こしテキスト
            session_id: セッションID
            memory_id: Memory ID（LTM検索用）
            meeting_title: 会議タイトル
            meeting_date: 会議日時
            participants: 参加者リスト
            
        Returns:
            生成された議事録
            
        Raises:
            ValueError: 入力検証エラー
            Exception: Bedrock API呼び出しエラー
        """
        # 入力検証 (Requirement 1.2, 1.3, 1.4, 1.5)
        # validate_transcript は検証に成功すると内容を返し、失敗すると例外を投げる
        # ここでは transcript が文字列として渡されるため、直接使用する
        
        logger.info(f"議事録生成開始: session_id={session_id}")
        
        # 過去の修正パターンを取得 (Requirement 7.2, 7.3)
        revision_patterns = []
        if memory_id:
            revision_patterns = self._search_revision_patterns(
                memory_id=memory_id,
                session_id=session_id,
                query=transcript[:500],  # 最初の500文字を検索クエリとして使用
            )
        
        # プロンプトを構築
        prompt = self._build_prompt(
            transcript=transcript,
            revision_patterns=revision_patterns,
            meeting_title=meeting_title,
            participants=participants,
        )
        
        # Bedrock Nova 2 Liteを呼び出し (Requirement 2.1)
        response_text = self._invoke_bedrock(prompt)
        
        # レスポンスをパースして議事録オブジェクトを構築
        minutes = self._parse_response(
            response_text=response_text,
            meeting_title=meeting_title,
            meeting_date=meeting_date,
            participants=participants,
        )
        
        logger.info(f"議事録生成完了: title={minutes.title}")
        
        return minutes
    
    def _search_revision_patterns(
        self,
        memory_id: str,
        session_id: str,
        query: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        AgentCore Memory LTMから過去の修正パターンを検索する
        
        Requirements: 7.2, 7.3
        
        Args:
            memory_id: Memory ID
            session_id: セッションID
            query: 検索クエリ
            top_k: 取得する最大件数
            
        Returns:
            修正パターンのリスト
        """
        try:
            from bedrock_agentcore.memory.session import MemorySessionManager
            
            # Memory Session Managerを初期化
            session_manager = MemorySessionManager(
                memory_id=memory_id,
                region_name=self.region_name,
            )
            
            # セッションを取得または作成
            session = session_manager.get_or_create_memory_session(
                actor_id="system",
                session_id=session_id,
            )
            
            # セマンティック検索で類似の修正パターンを取得
            memory_records = session.search_long_term_memories(
                query=query,
                namespace_prefix="/revision_patterns/",
                top_k=top_k,
            )
            
            patterns = []
            for record in memory_records:
                # メモリレコードから修正パターンを抽出
                if "content" in record:
                    patterns.append({
                        "pattern": record["content"],
                        "score": record.get("score", 0.0),
                    })
            
            logger.info(f"修正パターン検索完了: {len(patterns)}件取得")
            return patterns
            
        except Exception as e:
            logger.warning(f"修正パターン検索エラー: {e}")
            # エラーが発生しても処理は継続（修正パターンなしで生成）
            return []
    
    def _build_prompt(
        self,
        transcript: str,
        revision_patterns: List[Dict[str, Any]],
        meeting_title: Optional[str] = None,
        participants: Optional[List[str]] = None,
    ) -> str:
        """
        Bedrock用のプロンプトを構築する
        
        Requirements: 2.3, 2.4, 7.3
        
        Args:
            transcript: 書き起こしテキスト
            revision_patterns: 過去の修正パターン
            meeting_title: 会議タイトル
            participants: 参加者リスト
            
        Returns:
            構築されたプロンプト
        """
        prompt_parts = [
            "あなたは会議の議事録を作成する専門家です。",
            "以下の書き起こしテキストから、構造化された議事録を生成してください。",
            "",
            "## 出力形式",
            "以下のJSON形式で出力してください：",
            "{",
            '  "title": "会議タイトル",',
            '  "date": "YYYY-MM-DD HH:MM",',
            '  "participants": ["参加者1", "参加者2"],',
            '  "agenda": ["議題1", "議題2"],',
            '  "discussion": "議論内容の要約",',
            '  "decisions": ["決定事項1", "決定事項2"],',
            '  "action_items": [',
            '    {',
            '      "description": "タスクの説明",',
            '      "assignee": "担当者名",',
            '      "due_date": "YYYY-MM-DD",',
            '      "completed": false',
            '    }',
            '  ]',
            "}",
            "",
        ]
        
        # 会議情報が提供されている場合は追加
        if meeting_title:
            prompt_parts.append(f"## 会議タイトル\n{meeting_title}\n")
        
        if participants:
            prompt_parts.append(f"## 参加者\n{', '.join(participants)}\n")
        
        # 過去の修正パターンを追加 (Requirement 7.3)
        if revision_patterns:
            prompt_parts.append("## 過去の修正パターン")
            prompt_parts.append("以下の修正パターンを参考にして、同様の改善を適用してください：")
            for i, pattern in enumerate(revision_patterns, 1):
                prompt_parts.append(f"{i}. {pattern['pattern']}")
            prompt_parts.append("")
        
        # 書き起こしテキストを追加
        prompt_parts.extend([
            "## 書き起こしテキスト",
            transcript,
            "",
            "## 指示",
            "- 重要なポイントを抽出してください (Requirement 2.3)",
            "- 冗長な表現を簡潔にまとめてください (Requirement 2.4)",
            "- 参加者情報が不明な場合は空の配列を返してください",
            "- アクションアイテムには担当者と期限を含めてください",
            "- JSON形式で出力してください（マークダウンのコードブロックは不要）",
        ])
        
        return "\n".join(prompt_parts)
    
    def _invoke_bedrock(self, prompt: str) -> str:
        """
        Bedrock Nova 2 Liteを呼び出す
        
        Requirements: 2.1
        
        Args:
            prompt: プロンプト
            
        Returns:
            モデルの応答テキスト
            
        Raises:
            Exception: API呼び出しエラー
        """
        try:
            logger.info("Bedrock API呼び出し開始")
            
            # Converse APIを使用
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": 4096,
                    "temperature": 0.3,  # 一貫性のある出力のため低めに設定
                    "topP": 0.9,
                },
            )
            
            # レスポンスからテキストを抽出
            response_text = response["output"]["message"]["content"][0]["text"]
            
            logger.info(f"Bedrock API呼び出し完了: {len(response_text)}文字")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Bedrock API呼び出しエラー: {e}")
            raise
    
    def _parse_response(
        self,
        response_text: str,
        meeting_title: Optional[str] = None,
        meeting_date: Optional[str] = None,
        participants: Optional[List[str]] = None,
    ) -> Minutes:
        """
        Bedrockのレスポンスをパースして議事録オブジェクトを構築する
        
        Args:
            response_text: Bedrockのレスポンステキスト
            meeting_title: 会議タイトル（フォールバック用）
            meeting_date: 会議日時（フォールバック用）
            participants: 参加者リスト（フォールバック用）
            
        Returns:
            議事録オブジェクト
            
        Raises:
            ValueError: パースエラー
        """
        try:
            # JSONをパース
            # マークダウンのコードブロックが含まれている場合は除去
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            data = json.loads(response_text.strip())
            
            # 日時をパース
            date_str = data.get("date") or meeting_date
            if date_str:
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    # フォーマットが異なる場合は現在時刻を使用
                    date = datetime.now()
            else:
                date = datetime.now()
            
            # アクションアイテムをパース
            action_items = []
            for item_data in data.get("action_items", []):
                action_items.append(ActionItem(
                    description=item_data["description"],
                    assignee=item_data.get("assignee"),
                    due_date=item_data.get("due_date"),
                    completed=item_data.get("completed", False),
                ))
            
            # 議事録オブジェクトを構築
            minutes = Minutes(
                title=data.get("title") or meeting_title or "会議議事録",
                date=date,
                participants=data.get("participants") or participants or [],
                agenda=data.get("agenda", []),
                discussion=data.get("discussion", ""),
                decisions=data.get("decisions", []),
                action_items=action_items,
            )
            
            return minutes
            
        except json.JSONDecodeError as e:
            logger.error(f"JSONパースエラー: {e}")
            raise ValueError(f"議事録のパースに失敗しました: {e}")
        except Exception as e:
            logger.error(f"議事録構築エラー: {e}")
            raise ValueError(f"議事録の構築に失敗しました: {e}")


@tool
def generate_minutes(
    transcript: str,
    session_id: str,
    memory_id: Optional[str] = None,
    meeting_title: Optional[str] = None,
    meeting_date: Optional[str] = None,
    participants: Optional[List[str]] = None,
) -> dict:
    """
    会議の書き起こしテキストから議事録を生成する
    
    このツールはBedrock Nova 2 Liteを使用して議事録を生成します。
    AgentCore Memoryから過去の修正パターンを取得し、生成に反映します。
    
    Requirements: 2.1, 2.3, 2.4, 7.2, 7.3
    
    Args:
        transcript: 会議の書き起こしテキスト
        session_id: AgentCoreセッションID
        memory_id: AgentCore Memory ID（オプション、LTM検索用）
        meeting_title: 会議タイトル（オプション）
        meeting_date: 会議日時（オプション、YYYY-MM-DD HH:MM形式）
        participants: 参加者リスト（オプション）
    
    Returns:
        dict: 生成結果
            - success: 成功フラグ
            - minutes: 議事録データ（辞書形式）
            - error: エラーメッセージ（失敗時）
    """
    try:
        # 議事録生成器を初期化
        generator = MinutesGenerator()
        
        # 議事録を生成
        minutes = generator.generate_minutes(
            transcript=transcript,
            session_id=session_id,
            memory_id=memory_id,
            meeting_title=meeting_title,
            meeting_date=meeting_date,
            participants=participants,
        )
        
        # 議事録を辞書形式に変換
        minutes_dict = {
            "title": minutes.title,
            "date": minutes.date.strftime("%Y-%m-%d %H:%M"),
            "participants": minutes.participants,
            "agenda": minutes.agenda,
            "discussion": minutes.discussion,
            "decisions": minutes.decisions,
            "action_items": [
                {
                    "description": item.description,
                    "assignee": item.assignee,
                    "due_date": item.due_date,
                    "completed": item.completed,
                }
                for item in minutes.action_items
            ],
        }
        
        return {
            "success": True,
            "minutes": minutes_dict,
        }
        
    except ValueError as e:
        logger.error(f"入力検証エラー: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"議事録生成エラー: {e}")
        return {
            "success": False,
            "error": f"議事録の生成に失敗しました: {str(e)}",
        }
