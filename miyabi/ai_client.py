"""第2段階用のAPI接続境界。第1段階では外部APIへ通信しません。"""
import os


def api_key_configured() -> bool:
    """キーの内容はUIやログへ返さない。"""
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())
