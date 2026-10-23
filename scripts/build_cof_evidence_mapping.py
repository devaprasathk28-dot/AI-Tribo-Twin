"""Generate the derived COF evidence map; this never edits the protected raw CSV."""

from src.data.cof_evidence import build_cof_evidence_mapping

if __name__ == "__main__":
    print(build_cof_evidence_mapping())
