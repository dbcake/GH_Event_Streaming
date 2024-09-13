#!/bin/bash
up_validation=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5601/api/status)

file=./configured.txt

if [[ ! -f "$file" ]]
then
  echo "Config file does not exists."
  import_validation=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:5601/api/saved_objects/_import -H 'kbn-xsrf: true' --form file=@Kibana_objects_export.ndjson)
  touch configured.txt
fi

echo "--- Running Healthcheck script ---"
if [[ $up_validation == 200  ]]
then
  if [[ -f "$file" ]] || [[ $import_validation == 200 ]]
  then
    echo 0
    exit 0
  else
    echo 1
    exit 1
  fi
else
  echo 1
  exit 1
fi