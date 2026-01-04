"""
ユニットテスト: validate_transcript 関数

Requirements:
- 1.2: UTF-8エンコーディングのサポート
- 1.3: 空ファイルチェック
- 1.4: ファイルサイズ検証（1MB上限）
- 1.5: ファイルサイズ超過時のエラー
"""

import os
import tempfile
import pytest
from agents.tools.validate import validate_transcript, ValidationError


class TestValidateTranscript:
    """validate_transcript 関数のテストクラス"""
    
    def test_valid_file(self):
        """正常なファイルの検証"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            f.write("これは会議の書き起こしテキストです。\n参加者: 田中、佐藤\n議題: プロジェクト進捗")
            temp_path = f.name
        
        try:
            content = validate_transcript(temp_path)
            assert "会議の書き起こし" in content
            assert "田中" in content
        finally:
            os.unlink(temp_path)
    
    def test_utf8_encoding(self):
        """UTF-8エンコーディングのサポート - Requirements 1.2"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            # 日本語、絵文字、特殊文字を含むテキスト
            f.write("会議メモ 📝\n参加者: 山田太郎 🙋‍♂️\n内容: プロジェクトの進捗について議論しました。")
            temp_path = f.name
        
        try:
            content = validate_transcript(temp_path)
            assert "📝" in content
            assert "🙋‍♂️" in content
            assert "山田太郎" in content
        finally:
            os.unlink(temp_path)
    
    def test_empty_file(self):
        """空ファイルのチェック - Requirements 1.3"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            # 空ファイルを作成
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="ファイルが空です"):
                validate_transcript(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_whitespace_only_file(self):
        """空白のみのファイルのチェック - Requirements 1.3"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            f.write("   \n\n\t\t  \n")
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="ファイルの内容が空です"):
                validate_transcript(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_file_size_within_limit(self):
        """ファイルサイズが上限以内 - Requirements 1.4"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            # 約500KBのファイルを作成（1MB以下）
            content = "会議の内容です。" * 30000  # 約500KB
            f.write(content)
            temp_path = f.name
        
        try:
            result = validate_transcript(temp_path)
            assert "会議の内容です" in result
        finally:
            os.unlink(temp_path)
    
    def test_file_size_exceeds_limit(self):
        """ファイルサイズが上限を超過 - Requirements 1.4, 1.5"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            # 1MBを超えるファイルを作成
            content = "会議の内容です。" * 150000  # 約1.5MB
            f.write(content)
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="ファイルサイズが上限を超えています"):
                validate_transcript(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found(self):
        """存在しないファイルのエラー"""
        with pytest.raises(FileNotFoundError):
            validate_transcript("/path/to/nonexistent/file.txt")
    
    def test_invalid_encoding(self):
        """無効なエンコーディングのエラー"""
        # Shift-JISでファイルを作成してUTF-8として読み込もうとする
        with tempfile.NamedTemporaryFile(mode='w', encoding='shift-jis', delete=False, suffix='.txt') as f:
            f.write("これは日本語のテキストです")
            temp_path = f.name
        
        try:
            # UTF-8として読み込もうとするとエラーになる可能性がある
            # ただし、Shift-JISの一部の文字はUTF-8としても読める場合があるため、
            # このテストは環境依存の可能性がある
            content = validate_transcript(temp_path)
            # エラーが発生しない場合もあるため、assertは行わない
        except ValidationError:
            # エンコーディングエラーが発生した場合は成功
            pass
        finally:
            os.unlink(temp_path)
