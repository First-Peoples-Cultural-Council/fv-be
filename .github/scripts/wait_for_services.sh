#!/bin/bash

set -e

echo "Waiting for elasticsearch to be up."
for i in {1..20}; do
  status=$(curl -s http://localhsot:9200/_cluster/health | jq -r .status)
  if [[ "$status" == "green" ]] || [[ "$status" == "yellow" ]]; then
    echo "Elasticsearch is up with status: $status"
    break
  fi
  echo "Waiting ... ($i)"
  sleep 5
done
