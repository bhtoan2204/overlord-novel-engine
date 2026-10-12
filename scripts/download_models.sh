#!/usr/bin/env bash
# Downloads the verified Qwen GGUF files listed in config/models.yaml.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/models
download() {
  local name="$1"
  local url="$2"
  local target="data/models/${name}"
  if [[ -f "${target}" ]]; then
    echo "${name} already present"
    return
  fi
  echo "Downloading ${name}"
  curl -L --fail --retry 3 -C - -o "${target}.partial" "${url}"
  mv "${target}.partial" "${target}"
  sha256sum "${target}" | tee "${target}.sha256"
}
download "Qwen3-8B-Q4_K_M.gguf" "https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf"
download "Qwen3-4B-Q4_K_M.gguf" "https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf"
