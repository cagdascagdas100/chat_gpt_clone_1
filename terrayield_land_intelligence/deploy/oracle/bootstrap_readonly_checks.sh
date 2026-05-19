#!/usr/bin/env bash
set -euo pipefail

printf 'check=oracle_bootstrap_readonly\n'
printf 'timestamp_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'db_write=none\n'
printf 'ddl=none\n'
printf 'migration_apply=none\n'
printf 'prod_deploy=none\n'
printf 'secret_values_printed=false\n'

need() {
  if command -v "$1" >/dev/null 2>&1; then
    printf '%s=present\n' "$1"
  else
    printf '%s=missing\n' "$1"
  fi
}

need docker
need git
need curl

if docker compose version >/dev/null 2>&1; then
  printf 'docker_compose=present\n'
else
  printf 'docker_compose=missing\n'
fi

printf 'required_public_dns=terrayield.edalmo.com,api-terrayield.edalmo.com\n'
printf 'required_public_ports=80,443\n'
printf 'db_public_port_policy=closed\n'
printf 'backend_public_port_policy=closed_behind_caddy\n'
