import os

# 既存APIテストは認証なしアクセスを前提としているため、テスト時は明示的に無効化する。
os.environ.setdefault("SYNCSEMPHONE_DISABLE_AUTH", "1")
