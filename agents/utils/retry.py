"""リトライハンドラの実装。

このモジュールは、失敗した操作を自動的にリトライするデコレータを提供します。
指数バックオフを使用して、最大3回までリトライを試みます。
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

# ロガーの設定
logger = logging.getLogger(__name__)

# 型変数の定義
F = TypeVar('F', bound=Callable[..., Any])


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    on_final_failure: Optional[Callable[[Exception, str, Dict[str, Any]], None]] = None,
) -> Callable[[F], F]:
    """失敗した操作を自動的にリトライするデコレータ。
    
    指数バックオフを使用して、指定された回数までリトライを試みます。
    各リトライの間隔は base_delay * 2^attempt で計算されます。
    
    Args:
        max_retries: 最大リトライ回数（デフォルト: 3）
        base_delay: 基本遅延時間（秒）（デフォルト: 1.0）
        exceptions: リトライ対象の例外タプル（デフォルト: (Exception,)）
        on_final_failure: 最終的に失敗した場合のコールバック関数（オプション）
                         引数: (exception, function_name, context)
    
    Returns:
        デコレートされた関数
    
    Example:
        @with_retry(max_retries=3, base_delay=1.0)
        def call_api():
            # API呼び出し
            pass
        
        # エラー通知付き
        def notify_error(exc, func_name, context):
            send_error_notification(...)
        
        @with_retry(max_retries=3, on_final_failure=notify_error)
        def call_bedrock():
            # Bedrock API呼び出し
            pass
    
    Requirements:
        - 6.1: 最大3回のリトライ
        - 6.2: リトライ失敗時にSlackに通知
        - 6.3: エラー内容をログに記録
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        # リトライの場合はログ出力
                        logger.info(
                            f"リトライ {attempt}/{max_retries}: {func.__name__}"
                        )
                    
                    # 関数を実行
                    result = func(*args, **kwargs)
                    
                    # 成功した場合
                    if attempt > 0:
                        logger.info(
                            f"リトライ成功: {func.__name__} (試行回数: {attempt + 1})"
                        )
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # エラーログを記録
                    logger.error(
                        f"エラー発生 (試行 {attempt + 1}/{max_retries + 1}): "
                        f"{func.__name__} - {type(e).__name__}: {str(e)}"
                    )
                    
                    # 最後の試行でない場合は待機
                    if attempt < max_retries:
                        # 指数バックオフ: base_delay * 2^attempt
                        delay = base_delay * (2 ** attempt)
                        logger.info(f"{delay}秒待機してリトライします...")
                        time.sleep(delay)
                    else:
                        # 最後の試行でも失敗した場合
                        logger.error(
                            f"リトライ失敗: {func.__name__} - "
                            f"最大リトライ回数({max_retries})に達しました"
                        )
                        
                        # 最終失敗時のコールバックを実行
                        if on_final_failure:
                            try:
                                context = {
                                    "function_name": func.__name__,
                                    "max_retries": max_retries,
                                    "error_type": type(e).__name__,
                                }
                                on_final_failure(e, func.__name__, context)
                            except Exception as callback_error:
                                logger.error(
                                    f"エラー通知コールバックの実行に失敗: {str(callback_error)}"
                                )
            
            # すべてのリトライが失敗した場合、最後の例外を再送出
            raise last_exception
        
        return wrapper  # type: ignore
    
    return decorator
