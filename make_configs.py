"""Write Hawk scan configs for all non-opus55 MirrorCode swarm eval sets.
Split by the scanned models' serving provider (OpenAI-served sets may hit the cross-lab check), 10 sets per config
(Scout caps a job's concurrent judge calls at max_transcripts, so more, smaller jobs = more parallelism).
Usage: python make_configs.py GIT_SHA [max_transcripts=2] [memory=64Gi]"""
import csv, os, shutil, sys
sha = sys.argv[1]
mt = int(sys.argv[2]) if len(sys.argv) > 2 else 2
mem = sys.argv[3] if len(sys.argv) > 3 else "64Gi"
model = {r["eval_set_id"]: r["model"] for r in csv.DictReader(open("../sets.csv"))}
OAI = {"openai/gpt-6-luna", "openai/gpt-6.1-sol"}
all_ids = sorted(d for d in os.listdir("../logs") if d.startswith(("mc-", "mirrorcode-")) and "opus55" not in d)
shutil.rmtree("configs", ignore_errors=True); os.makedirs("configs")
n = 0
for tag, ids in (("or", [i for i in all_ids if model.get(i) not in OAI]), ("oai", [i for i in all_ids if model.get(i) in OAI])):
    for k in range(0, len(ids), 10):
        chunk = ids[k:k + 10]; name = f"mc-swarm-audit-{tag}-{k // 10:02d}"; n += 1
        srcs = "\n".join(f"    - eval_set_id: {i}" for i in chunk)
        open(f"configs/{name}.yaml", "w").write(f"""name: {name}
scanners:
  - package: "git+https://github.com/jrh-mann/mirrorcode-swarm-scanners@{sha}"
    name: mirrorcode_swarm_scanners
    items:
      - name: swarm_audit
models:
  - package: openai
    name: openrouter
    items:
      - name: openrouter/anthropic/claude-haiku-5.5
        args:
          config:
            cache_prompt: false
max_transcripts: {mt}
runner:
  memory: {mem}
transcripts:
  sources:
{srcs}
""")
print(len(all_ids), "sets ->", n, "configs")
