"""Small helper to generate synthetic transcript files for local testing.

Usage:
    python utils/generate_synthetic_transcripts.py --count 10 --outdir data/sample_transcripts

The script creates alternating .txt and .json transcript files with basic metadata.
"""
import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


TEMPLATES = [
    (
        "support",
        [
            "Agent: Hello, thanks for calling. How can I help?",
            "Customer: I'm having trouble with my service.",
            "Agent: I'll run diagnostics and escalate if needed.",
            "Customer: Thank you."
        ],
    ),
    (
        "billing",
        [
            "Agent: Good morning, this is billing. How may I assist?",
            "Customer: I have a question about a charge on my bill.",
            "Agent: Let me look that up and explain the details.",
            "Customer: Great, thanks."
        ],
    ),
    (
        "sales",
        [
            "Agent: Hi, this is sales — are you interested in our upgrade?",
            "Customer: Can you tell me the differences in plans?",
            "Agent: Sure: plan A includes..., plan B includes...",
            "Customer: I'll think about it."
        ],
    ),
]


def make_transcript(idx: int):
    kind, lines = random.choice(TEMPLATES)
    start = datetime.utcnow() - timedelta(days=random.randint(0, 30), minutes=random.randint(0, 120))
    duration = random.randint(60, 600)
    transcript = "\n".join(lines)
    call_id = f"synthetic_{idx:04d}"
    return {
        "call_id": call_id,
        "agent": random.choice(["Alex", "Priya", "Lena", "Carlos", "Sarah"]),
        "customer": random.choice(["Jordan", "Taylor", "Sam", "Maya", "Tom"]),
        "start_time": start.isoformat() + "Z",
        "duration_seconds": duration,
        "transcript": transcript,
        "tags": [kind],
        "resolution": "unknown",
        "success": True,
        "sentiment": random.choice(["neutral", "positive", "concerned"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--outdir", type=str, default="data/sample_transcripts")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for i in range(1, args.count + 1):
        data = make_transcript(i)
        if i % 2 == 0:
            # write JSON with metadata
            path = outdir / f"{data['call_id']}.json"
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        else:
            # write plain text transcript
            path = outdir / f"{data['call_id']}.txt"
            with path.open("w", encoding="utf-8") as f:
                f.write(data["transcript"])

    print(f"Generated {args.count} synthetic transcripts in {outdir}")


if __name__ == "__main__":
    main()
