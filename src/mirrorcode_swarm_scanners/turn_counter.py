"""Structural (no-LLM) scanner: per agent span, count model calls (turns) and output tokens from event metadata.
One Result per agent_k span (label = span name). Reads no message content."""
from inspect_scout import Result, Scanner, Transcript, scanner


@scanner(events=["model", "span_begin"])
def turn_counter() -> Scanner[Transcript]:
    async def scan(transcript: Transcript) -> list[Result]:
        spans = {e.id: e for e in transcript.events if e.event == "span_begin"}

        def agent_of(span_id):
            seen = set()
            while span_id and span_id not in seen:
                seen.add(span_id)
                sp = spans.get(span_id)
                if sp is None:
                    return None
                if sp.type == "agent":
                    return sp.name
                span_id = sp.parent_id
            return None

        stats: dict[str, dict] = {}
        for e in transcript.events:
            if e.event != "model":
                continue
            a = agent_of(e.span_id)
            if a is None:
                continue
            s = stats.setdefault(a, {"turns": 0, "output_tokens": 0, "reasoning_tokens": 0})
            s["turns"] += 1
            u = e.output.usage if e.output else None
            if u:
                s["output_tokens"] += u.output_tokens or 0
                s["reasoning_tokens"] += u.reasoning_tokens or 0
        return [Result(label=a, value=v) for a, v in sorted(stats.items())] or [Result(value={"turns": 0})]

    return scan
