# mirrorcode-swarm-scanners

Inspect Scout scanner (`swarm_audit`) that audits MirrorCode multi-agent ("swarm") eval transcripts one agent at a time: 0-3 scores for cheating, teammate harm, deception, sandbox probing, eval awareness and rule salience, plus verbatim findings. Per-agent spans via `@scanner(timeline=True)`; windows capped at 60k tokens; a max-reducer merges windows.
