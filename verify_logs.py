"""Prove the saved sensor logs match the hashes stored on the blockchain."""
import argparse
import json
import os
import sys
import requests
from eth_hash.auto import keccak
def window_hash(readings):
"""Must match the backend: keccak256 of canonical JSON."""
payload = json.dumps(readings, separators=(",", ":"), sort_keys=True)
return "0x" + keccak(payload.encode("utf-8")).hex()
def main():
p = argparse.ArgumentParser()
p.add_argument("--batch", required=True)
p.add_argument("--backend", default="http://127.0.0.1:5000")
p.add_argument("--file", default="anchored_windows.json")
p.add_argument(
"--tamper", action="store_true", help="edit one reading first to show a mismatch"
)
a = p.parse_args()
if not os.path.exists(a.file):
sys.exit("No %s here. Run simulator.py first, from this same folder." % a.file)
with open(a.file) as f:
windows = [w for w in json.load(f) if w["batch_id"] == a.batch]
if not windows:
sys.exit("No saved windows for batch %s in %s" % (a.batch, a.file))
res = requests.get("%s/verify/%s" % (a.backend, a.batch), timeout=15).json()
if not res.get("ok"):
sys.exit("Backend says: %s" % res.get("error"))
on_chain = {row["data_hash"].lower() for row in res["temp_logs"]}
if a.tamper:
windows[0]["readings"][0]["temp"] = 5.0
print("(tamper mode: first reading of window 1 changed to 5.0 C)\n")
bad = 0
for i, w in enumerate(windows, 1):
h = window_hash(w["readings"]).lower()
ok = h in on_chain
bad += 0 if ok else 1
print("window %d: %s %s" % (i, "MATCH print(
"\n%s"
% (
" if ok else "MISMATCH", h[:22] + "..."))
"All logs match the blockchain."
if bad == 0
else "%d window(s) do NOT match: the log was altered." % bad
)
)
if __name__ == "__main__":
main()