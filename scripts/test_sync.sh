#!/usr/bin/env bash
set -euo pipefail

SPACE_ID="7612135385660967897"

if [ -z "${FEISHU_ACCESS_TOKEN:-}" ]; then
  echo "FEISHU_ACCESS_TOKEN is required"
  exit 1
fi

payload='{
  "title": "Test Page",
  "parent_wiki_token": "",
  "obj_type": "doc"
}'

curl -sS -X POST "https://open.feishu.cn/open-apis/wiki/v2/spaces/${SPACE_ID}/nodes" \
  -H "Authorization: Bearer ${FEISHU_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "${payload}"

echo
