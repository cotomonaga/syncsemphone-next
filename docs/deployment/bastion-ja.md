# Bastion Deployment (Non-Disruptive)

この手順は既存サービスを停止せずに `syncsem.senju-tech.com` を追加するためのものです。

## 前提

- Ubuntu bastion
- nginx / systemd が利用可能
- `node` / `npm` / `python3` / `git` が利用可能
- リポジトリ: `https://github.com/cotomonaga/syncsemphone-next.git`

## ファイル配置

- deploy: `infra/deploy/deploy_bastion.sh`
- rollback: `infra/deploy/rollback_bastion.sh`
- systemd: `infra/systemd/syncsemphone-next-api.service`
- nginx: `infra/nginx/syncsemphone-next.conf`
- env: `infra/env/api.env.example`
- password hash tool: `infra/tools/generate_password_hash.py`

## 1. パスワードハッシュ作成

```bash
python3 infra/tools/generate_password_hash.py --username admin --password 'strong-password'
```

生成された JSON を `SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON` に設定してください。

## 2. デプロイ実行

```bash
sudo APP_USER=tomonaga APP_GROUP=tomonaga BRANCH=main \
  ./infra/deploy/deploy_bastion.sh
```

このスクリプトは次を行います。

- 既存設定と current リリースのバックアップ
- `/opt/syncsemphone-next/releases/<timestamp>` へ新規展開
- API venv 構築・依存導入
- Web 本番ビルド (`VITE_API_BASE_URL=/api`)
- systemd/nginx 設定配置
- `syncsemphone-next-api.service` 起動
- nginx reload

## 3. env 設定

初回のみ `/etc/syncsemphone-next/api.env` が自動作成されます。必ず編集してください。

```bash
sudoedit /etc/syncsemphone-next/api.env
```

最低限:

- `SYNCSEMPHONE_SESSION_SECRET` (32文字以上)
- `SYNCSEMPHONE_AUTH_PASSWORD_HASHES_JSON`
- `SYNCSEMPHONE_ALLOWED_HOSTS=syncsem.senju-tech.com,127.0.0.1,localhost`
- `SYNCSEMPHONE_CORS_ORIGINS=https://syncsem.senju-tech.com`

## 4. 疎通確認

```bash
curl -fsS http://127.0.0.1:18100/v1/healthz
curl -fsS -H "Host: syncsem.senju-tech.com" http://127.0.0.1/_healthz
```

## 5. TLS 適用（必要時）

certbot を使う場合:

```bash
sudo certbot --nginx -d syncsem.senju-tech.com
```

## 6. ロールバック

```bash
sudo ./infra/deploy/rollback_bastion.sh /opt/syncsemphone-next/releases/<timestamp>
```
