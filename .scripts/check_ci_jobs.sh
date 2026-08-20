#!/bin/bash
# Fetch job conclusions for the latest CI run of salauddinmir/Misty-Ai.
RUN=$(gh run list --repo salauddinmir/Misty-Ai --limit 1 --json databaseId --jq '.[0].databaseId')
echo "run_id=$RUN"
gh api repos/salauddinmir/Misty-Ai/actions/runs/$RUN/jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
