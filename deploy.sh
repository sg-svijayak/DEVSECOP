#!/usr/bin/env bash
# Usage: ./deploy.sh <env> <image>
# TODO: implement for your hosting target (Azure Web App, ECS, AKS, ...).
# Fetch secrets from AKeyless/OIDC; never hard-code credentials.
set -euo pipefail
echo "Would deploy $2 to $1"
