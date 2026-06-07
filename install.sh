#!/usr/bin/env bash
# sfu-converter agent installer shim.

set -euo pipefail

REPO="bounchich1/sfu_converter"

if ! command -v node >/dev/null 2>&1; then
  echo "sfu-converter: Node.js (>=18) required. Install Node.js from https://nodejs.org." >&2
  exit 1
fi

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [ "$NODE_MAJOR" -lt 18 ]; then
  echo "sfu-converter: Node $NODE_MAJOR too old. Need Node >=18." >&2
  exit 1
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]:-}")" 2>/dev/null && pwd)" || here=""
if [ -n "$here" ] && [ -f "$here/bin/install.js" ]; then
  exec node "$here/bin/install.js" "$@"
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "sfu-converter: npx required; reinstall Node.js >=18." >&2
  exit 1
fi

exec npx -y "github:$REPO" "$@"
