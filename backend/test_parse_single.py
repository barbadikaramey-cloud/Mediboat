import sys
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)

from pathlib import Path
import app.config  # ensures cache paths are set
from app.ingestion.parse import parse_document

print("Starting parse test...", flush=True)
f = Path("data/docs/billing/claim_submission_guide.md")
chunks = parse_document(f, "billing")
print(f"SUCCESS: Parsed {len(chunks)} chunks from {f.name}", flush=True)
for i, c in enumerate(chunks[:3]):
    print(f"Chunk {i+1} [{c.chunk_type}]: section='{c.section_title}'", flush=True)
    print(f"  {c.text[:120]}...\n", flush=True)

