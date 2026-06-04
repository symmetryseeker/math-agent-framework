"""Diagnose why DeepSeek-V3.2 MAF regressed on hard problems."""
import json, os

report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "reports", "maf_vs_raw_20260603_174121.json")
with open(report_path, "r", encoding="utf-8") as f:
    r = json.load(f)

ds = r["results"]["DeepSeek-V3.2"]
hard = [d for d in ds["details"] if d.get("difficulty") == "hard"]

print("DeepSeek-V3.2 HARD problems (n=%d):" % len(hard))
print("=" * 70)
regressions = 0

for i, d in enumerate(hard):
    raw = round(d.get("raw_score", 0) * 100)
    maf = round(d.get("maf_score", 0) * 100)
    verified = d.get("maf_verified", "N/A")
    computed = str(d.get("maf_computed", ""))[:80]
    problem = str(d.get("problem", ""))[:80]
    improvement = maf - raw

    print("[%d] %s  (raw=%d%%, maf=%d%%, d=%+dpp, verified=%s)" %
          (i+1, d["id"], raw, maf, improvement, verified))
    print("    Problem: %s" % problem)
    if computed:
        print("    Computed: %s" % computed)
    if improvement < 0:
        regressions += 1
        print("    *** REGRESSION: score DROPPED by %dpp ***" % abs(improvement))
        print("    Root cause hypothesis:")
        if not verified:
            print("      -> MAF verification FAILED: symbolic check rejected answer")
        else:
            print("      -> MAF produced CORRECT but DIFFERENT answer from expected")
    print()

# Also check overall stats
print("=" * 70)
print("Summary:")
print("  Hard problems: %d" % len(hard))
print("  Regressions: %d (%.0f%%)" % (regressions, regressions/max(len(hard),1)*100))

# Check if the raw "perfect score" was genuine
raw_perfect = [d for d in hard if d.get("raw_score", 0) >= 1.0]
print("  Raw perfect scores: %d problems" % len(raw_perfect))
for d in raw_perfect:
    print("    %s: raw=100%% but MAF verified=%s" % (d["id"], d.get("maf_verified")))

# Check the raw answer field
print()
print("Raw answer field analysis:")
for d in hard:
    raw_ans = str(d.get("raw_answer", ""))[:50]
    maf_ans = str(d.get("maf_answer", ""))[:50]
    print("  %s: raw_answer='%s'  maf_answer='%s'" % (d["id"], raw_ans, maf_ans))
