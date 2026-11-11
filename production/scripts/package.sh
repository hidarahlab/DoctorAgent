#!/bin/sh
# Builds the submission zip (code + requirements + presentation), without secrets or generated files.
set -e
cd "$(dirname "$0")/.."
mkdir -p dist
OUT="dist/DoctorAgent_RoleAI_TechnicalTest.zip"
rm -f "$OUT"
zip -rq "$OUT" \
  app.py config.py requirements.txt README.md .env.example .gitignore .streamlit/config.toml \
  doctor_agent tests scripts/smoke_test.py \
  eval/questions.json eval/run_eval.py eval/results \
  data/chunks.json \
  docs \
  -x "*__pycache__*" "*.pyc" "*.DS_Store"
echo "$OUT"
unzip -l "$OUT" | tail -1
