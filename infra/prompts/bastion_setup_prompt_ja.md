# Bastion設定依頼プロンプト（貼り付け用）

以下をそのまま別エージェントに渡してください。

```text
Ubuntu bastion に syncsemphone-next を新規デプロイしてください。
既存サービスは絶対に停止しないこと。変更は新規ポート/新規サービス名のみで行うこと。

前提:
- リポジトリ: https://github.com/cotomonaga/syncsemphone-next.git
- ブランチ: main
- ドメイン: syncsem.senju-tech.com
- API内部待受: 127.0.0.1:18100
- 公開ルール: /api/* -> FastAPI, それ以外 -> React静的配信

必須要件:
1) 変更前バックアップ
- /etc/nginx/sites-available/syncsemphone-next.conf
- /etc/systemd/system/syncsemphone-next-api.service
- /etc/syncsemphone-next/api.env
- 現在の /opt/syncsemphone-next/current があればスナップショット保存

2) デプロイ
- /opt/syncsemphone-next/releases/<timestamp> へ clone
- Python venv を /opt/syncsemphone-next/shared/venv に作成し API依存をインストール
- apps/web で `VITE_API_BASE_URL=/api npm run build`
- /opt/syncsemphone-next/current を新リリースへ切替

3) 設定反映
- infra/systemd/syncsemphone-next-api.service を /etc/systemd/system/ へ配置
- infra/nginx/syncsemphone-next.conf を /etc/nginx/sites-available/ へ配置し sites-enabled へリンク
- /etc/syncsemphone-next/api.env が未作成なら infra/env/api.env.example から作成
- APIポート placeholder `__API_PORT__` を 18100 に置換

4) 起動確認
- `systemctl daemon-reload`
- `systemctl enable --now syncsemphone-next-api.service`
- `nginx -t && systemctl reload nginx`
- `curl -fsS http://127.0.0.1:18100/v1/healthz`
- `curl -fsS -H "Host: syncsem.senju-tech.com" http://127.0.0.1/_healthz`

5) TLS
- 必要なら certbot で syncsem.senju-tech.com 証明書を取得し nginx へ適用

6) 報告
- 実行したコマンド
- 変更ファイル
- バックアップ保存先
- systemd/nginx の状態
- 最終疎通結果
```
