#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "error: run as root (sudo)" >&2
  exit 1
fi

APP_ROOT=${APP_ROOT:-/opt/syncsemphone-next}
TARGET_RELEASE=${1:-}

if [[ -z "${TARGET_RELEASE}" ]]; then
  echo "usage: sudo ./infra/deploy/rollback_bastion.sh /opt/syncsemphone-next/releases/<timestamp>" >&2
  exit 1
fi

if [[ ! -d "${TARGET_RELEASE}" ]]; then
  echo "error: target release not found: ${TARGET_RELEASE}" >&2
  exit 1
fi

ln -sfn "${TARGET_RELEASE}" "${APP_ROOT}/current"
systemctl restart syncsemphone-next-api.service
nginx -t
systemctl reload nginx

echo "Rollback complete."
echo "Current release: ${TARGET_RELEASE}"
