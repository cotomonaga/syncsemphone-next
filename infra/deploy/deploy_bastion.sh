#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "error: run as root (sudo)" >&2
  exit 1
fi

APP_USER=${APP_USER:-tomonaga}
APP_GROUP=${APP_GROUP:-${APP_USER}}
APP_ROOT=${APP_ROOT:-/opt/syncsemphone-next}
REPO_URL=${REPO_URL:-https://github.com/cotomonaga/syncsemphone-next.git}
BRANCH=${BRANCH:-main}
API_PORT=${API_PORT:-18100}
SERVER_NAME=${SERVER_NAME:-syncsem.senju-tech.com}
DEPLOY_TS=$(date +%Y%m%d-%H%M%S)
created_env=0

if ! id "${APP_USER}" >/dev/null 2>&1; then
  echo "error: user ${APP_USER} does not exist" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required" >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required" >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm is required for web build" >&2
  exit 1
fi
if ! command -v nginx >/dev/null 2>&1; then
  echo "error: nginx is required" >&2
  exit 1
fi

mkdir -p "${APP_ROOT}/releases" "${APP_ROOT}/shared" "${APP_ROOT}/backups/${DEPLOY_TS}"

if [[ -L "${APP_ROOT}/current" ]]; then
  current_target=$(readlink -f "${APP_ROOT}/current" || true)
  if [[ -n "${current_target}" && -d "${current_target}" ]]; then
    cp -a "${current_target}" "${APP_ROOT}/backups/${DEPLOY_TS}/previous-release"
  fi
fi

if [[ -f /etc/systemd/system/syncsemphone-next-api.service ]]; then
  cp -a /etc/systemd/system/syncsemphone-next-api.service \
    "${APP_ROOT}/backups/${DEPLOY_TS}/syncsemphone-next-api.service.bak"
fi
if [[ -f /etc/nginx/sites-available/syncsemphone-next.conf ]]; then
  cp -a /etc/nginx/sites-available/syncsemphone-next.conf \
    "${APP_ROOT}/backups/${DEPLOY_TS}/syncsemphone-next.conf.bak"
fi
if [[ -f /etc/syncsemphone-next/api.env ]]; then
  cp -a /etc/syncsemphone-next/api.env \
    "${APP_ROOT}/backups/${DEPLOY_TS}/api.env.bak"
fi

release_dir="${APP_ROOT}/releases/${DEPLOY_TS}"
git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${release_dir}"

python3 -m venv "${APP_ROOT}/shared/venv"
"${APP_ROOT}/shared/venv/bin/python" -m pip install --upgrade pip setuptools wheel
"${APP_ROOT}/shared/venv/bin/python" -m pip install -e "${release_dir}/apps/api"

pushd "${release_dir}/apps/web" >/dev/null
npm ci
VITE_API_BASE_URL=/api npm run build
popd >/dev/null

ln -sfn "${release_dir}" "${APP_ROOT}/current"
ln -sfn "${APP_ROOT}/shared/venv" "${APP_ROOT}/venv"

install -d -m 0750 -o root -g "${APP_GROUP}" /etc/syncsemphone-next
if [[ ! -f /etc/syncsemphone-next/api.env ]]; then
  install -m 0640 -o root -g "${APP_GROUP}" \
    "${release_dir}/infra/env/api.env.example" /etc/syncsemphone-next/api.env
  echo "info: created /etc/syncsemphone-next/api.env (edit secrets before exposing to internet)"
  created_env=1
fi

install -m 0644 -o root -g root \
  "${release_dir}/infra/systemd/syncsemphone-next-api.service" \
  /etc/systemd/system/syncsemphone-next-api.service

install -d -m 0755 /etc/nginx/sites-available /etc/nginx/sites-enabled
install -m 0644 -o root -g root \
  "${release_dir}/infra/nginx/syncsemphone-next.conf" \
  /etc/nginx/sites-available/syncsemphone-next.conf
ln -sfn /etc/nginx/sites-available/syncsemphone-next.conf \
  /etc/nginx/sites-enabled/syncsemphone-next.conf

sed -i "s|__API_PORT__|${API_PORT}|g" /etc/systemd/system/syncsemphone-next-api.service
sed -i "s|__APP_USER__|${APP_USER}|g" /etc/systemd/system/syncsemphone-next-api.service
sed -i "s|__APP_GROUP__|${APP_GROUP}|g" /etc/systemd/system/syncsemphone-next-api.service
sed -i "s|__API_PORT__|${API_PORT}|g" /etc/nginx/sites-available/syncsemphone-next.conf
sed -i "s|__SERVER_NAME__|${SERVER_NAME}|g" /etc/nginx/sites-available/syncsemphone-next.conf

chown -R "${APP_USER}:${APP_GROUP}" "${APP_ROOT}"

systemctl daemon-reload
systemctl enable syncsemphone-next-api.service
if [[ "${created_env}" -eq 0 ]]; then
  systemctl restart syncsemphone-next-api.service
else
  echo "info: first deploy detected. service restart skipped until /etc/syncsemphone-next/api.env is edited."
fi

nginx -t
systemctl reload nginx

echo
if [[ "${created_env}" -eq 0 ]]; then
  systemctl --no-pager --full status syncsemphone-next-api.service | sed -n "1,30p"
else
  echo "next:"
  echo "  sudoedit /etc/syncsemphone-next/api.env"
  echo "  sudo systemctl restart syncsemphone-next-api.service"
  echo "  sudo systemctl --no-pager --full status syncsemphone-next-api.service | sed -n '1,30p'"
fi
echo
echo "Deploy complete."
echo "Release: ${release_dir}"
echo "Backup:  ${APP_ROOT}/backups/${DEPLOY_TS}"
