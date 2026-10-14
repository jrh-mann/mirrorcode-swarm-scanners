"""Pull swarm_audit results for every finished mc-swarm-audit scan straight from S3, light columns only
(skips the heavy input / input_data / scan_events columns), and expand each transcript's resultset into
one row per agent span -> results/agent_results.jsonl (+ results/scans.json manifest).

Run from ~/Documents/generality with the read-only eb-monitor creds loaded (see generality-aws skill):
  set -a && . ./.env && set +a && export AWS_SECRET_ACCESS_KEY="${AWS_API_KEY:-$AWS_SECRET_ACCESS_KEY}" AWS_DEFAULT_REGION=eu-west-2
  analysis/mirrorcode-swarm/scout/.venv/bin/python -u analysis/mirrorcode-swarm/hawk_scanners/fetch_results.py
"""
import json, os, subprocess, urllib.request
import pyarrow.fs as pafs
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
COLS = ["transcript_id", "transcript_source_uri", "transcript_model", "transcript_task_id", "transcript_error",
        "uuid", "value_type", "value", "explanation", "scan_error"]

tok = subprocess.check_output(["hawk", "auth", "access-token"], text=True, stderr=subprocess.DEVNULL).strip()
req = urllib.request.Request("https://api.hawk.hawk.generalitylabs.ai/meta/scans?limit=200&search=mc-swarm-audit",
                             headers={"Authorization": f"Bearer {tok}"})
scans = json.load(urllib.request.urlopen(req, timeout=60))["items"]
s3 = pafs.S3FileSystem(region="eu-west-2", access_key=os.environ["AWS_ACCESS_KEY_ID"],
                       secret_key=os.environ["AWS_SECRET_ACCESS_KEY"])
os.makedirs(OUT, exist_ok=True)
rows, manifest = [], []
for sc in scans:
    path = sc["location"].replace("s3://", "") + "/swarm_audit.parquet"
    try:
        t = pq.ParquetFile(path, filesystem=s3).read(columns=COLS).to_pylist()
    except Exception as e:
        manifest.append({"job_id": sc["job_id"], "location": sc["location"], "error": repr(e)[:200]}); continue
    manifest.append({"job_id": sc["job_id"], "location": sc["location"], "transcripts": len(t), "errors": sc.get("errors")})
    for r in t:
        run = (r["transcript_source_uri"] or "").split("/evals/")[-1].split("/")[0] if r["transcript_source_uri"] else None
        base = {"job_id": sc["job_id"], "run": run, "log": r["transcript_source_uri"], "transcript_id": r["transcript_id"],
                "model": r["transcript_model"], "task_id": r["transcript_task_id"], "transcript_error": r["transcript_error"],
                "scan_error": r["scan_error"]}
        v = json.loads(r["value"]) if isinstance(r["value"], str) else r["value"]
        items = v if r["value_type"] == "resultset" and isinstance(v, list) else [{"uuid": r["uuid"], "value": v, "explanation": r["explanation"]}]
        for k, it in enumerate(items):
            rows.append({**base, "span_index": k, "result_uuid": it.get("uuid"), "value": it.get("value"),
                         "summary": it.get("explanation"), "references": it.get("references")})
with open(os.path.join(OUT, "agent_results.jsonl"), "w") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
json.dump(manifest, open(os.path.join(OUT, "scans.json"), "w"), indent=1)
print(f"{len(scans)} scans, {sum(m.get('transcripts', 0) for m in manifest)} transcripts, {len(rows)} agent rows, "
      f"{sum(1 for m in manifest if 'error' in m)} unreadable")
