"""Write Hawk scan configs: all non-opus55 MirrorCode swarm eval sets, 20 per config (Hawk's cap).
Usage: python make_configs.py GIT_SHA"""
import os, sys
sha = sys.argv[1]
ids = sorted(d for d in os.listdir("../logs") if d.startswith(("mc-", "mirrorcode-")) and "opus55" not in d)
os.makedirs("configs", exist_ok=True)
for k in range(0, len(ids), 20):
    chunk = ids[k:k + 20]
    srcs = "\n".join(f"    - eval_set_id: {i}" for i in chunk)
    open(f"configs/scan_{k // 20:02d}.yaml", "w").write(f"""name: mc-swarm-audit-{k // 20:02d}
scanners:
  - package: "git+https://github.com/jrh-mann/mirrorcode-swarm-scanners@{sha}"
    name: mirrorcode_swarm_scanners
    items:
      - name: swarm_audit
models:
  - package: openai
    name: openrouter
    items:
      - name: anthropic/claude-haiku-5.5
max_transcripts: 2
runner:
  memory: 64Gi
transcripts:
  sources:
{srcs}
""")
print(len(ids), "eval sets ->", len(range(0, len(ids), 20)), "configs")
