"""
書き起こしテキストの検証ツール

Requirements:
- 1.2: UTF-8エンコーディングのサポート
- 1.3: 空ファイルチェック
- 1.4: ファイルサイズ検証（1MB上限）
- 1.5: ファイルサイズ超過時のエラー
"""

import os
from typing import Optional


class ValidationError(Exception):
    """検証エラーを表す例外クラス"""
    pass


def validate_transcript(file_path: str) -> str:
    """
    書き起こしテキストファイルを検証し、内容を返す
    
    Args:
        file_path: 検証対象のファイルパス
        
    Returns:
        str: ファイルの内容（UTF-8デコード済み）
        
    Raises:
        ValidationError: ファイルが空、サイズ超過、またはエンコーディングエラーの場合
        FileNotFoundError: ファイルが存在しない場合
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    
    # ファイルサイズの検証（1MB = 1,048,576 bytes）
    MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB
    file_size = os.path.getsize(file_path)
    
    if file_size == 0:
        raise ValidationError("ファイルが空です")
    
    if file_size > MAX_FILE_SIZE:
        raise ValidationError(
            f"ファイルサイズが上限を超えています: {file_size} bytes (上限: {MAX_FILE_SIZE} bytes)"
        )
    
    # UTF-8エンコーディングでファイルを読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError as e:
        raise ValidationError(f"UTF-8エンコーディングエラー: {str(e)}")
    
    # 読み込んだ内容が空でないことを再確認
    if not content.strip():
        raise ValidationError("ファイルの内容が空です")
    
    return content
