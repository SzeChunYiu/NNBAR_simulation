.PHONY: supervisor supervisor-stop supervisor-status supervisor-logs

# Start (or restart) the nnbar codex-supervisor batch.
# Workflow: edit .codex-supervisor.toml to point at the new prompts file,
# then run `make supervisor`.
supervisor:
	@echo "Starting nnbar supervisor (session: nnbar-gpu-batch)..."
	@rm -f ~/.codex-supervisor-nnbar-gpu-batch.disabled
	CODEX_SUPERVISOR_SESSION=nnbar-gpu-batch \
	CODEX_SUPERVISOR_PROMPTS=scripts/codex-supervisor/nnbar-gpu-batch-prompts.txt \
	CODEX_SUPERVISOR_ON_COMPLETE=queue \
	CODEX_SUPERVISOR_CONTINUOUS_LANES="worker-0 worker-1 worker-2 planner" \
	CODEX_SUPERVISOR_PLANNER=0 \
	~/codex-supervisor.sh start --no-attach

supervisor-stop:
	CODEX_SUPERVISOR_SESSION=nnbar-gpu-batch ~/codex-supervisor.sh stop --no-disable

supervisor-status:
	CODEX_SUPERVISOR_SESSION=nnbar-gpu-batch ~/codex-supervisor.sh status

supervisor-logs:
	CODEX_SUPERVISOR_SESSION=nnbar-gpu-batch ~/codex-supervisor.sh logs -f
