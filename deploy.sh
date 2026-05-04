#!/usr/bin/env bash
set -euo pipefail

echo "==> git pull"
git pull

echo "==> docker-compose down"
docker-compose down

echo "==> docker-compose up --build -d"
docker-compose up --build -d

echo "==> 서비스 상태 확인"
docker-compose ps
