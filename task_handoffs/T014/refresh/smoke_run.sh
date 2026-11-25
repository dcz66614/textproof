#!/bin/bash
# T014R2 offline smoke: fresh venv, install the NEW release wheel built
# from freeze commit 1f02358, rebuild the dictionary in-package, then run
# check / serve / verify-s0 with no checkout on the path.
# Wheel: release/textproof-1.0.0-py3-none-any.whl
#   SHA-256 cffd51836449a83efeeb9d407582b26c358526ba374d685cdb925e2f7dd17c0c
#   (32 entries: UI + 3 models + validator + setup module, no dictionary).
# All evidence lands in task_handoffs/T014/pkg/ (superseding the
# T013-U01 smoke, which used a wheel built from 717b813).
set -u
W=~/workspace/p033-textproof-t014-refresh
VENV=$W/tmp/venv-offline
EVID=$W/task_handoffs/T014/pkg
SMOKE=$W/tmp/smoke
export TMPDIR=$W/tmp
mkdir -p "$SMOKE" "$W/tmp"
unset PYTHONPATH
export PIP_DISABLE_PIP_VERSION_CHECK=1

rm -rf "$VENV"
python3 -m venv "$VENV"
VPY=$VENV/bin/python
VTP=$VENV/bin/textproof

"$VPY" -m pip install --no-index --find-links "$W/release/wheelhouse" \
  "$W/release/textproof-1.0.0-py3-none-any.whl" \
  > "$EVID/offline_install.log" 2>&1
echo "offline_install_exit=$?"

"$VTP" --help > "$EVID/smoke_help.log" 2>&1
echo "textproof_help_exit=$?"

"$VTP" version > "$EVID/smoke_version.json" 2> "$EVID/smoke_version.err"
echo "textproof_version_exit=$?"

"$VPY" -m textproof.setup_dictionary > "$EVID/setup_dictionary_install.log" 2>&1
echo "setup_dictionary_exit=$?"

cp "$W/tests/fixtures/s0/TP-S0-ZH-001.png" "$SMOKE/poster.png"
printf '限时优惠' > "$SMOKE/expected.txt"
"$VTP" check --image "$SMOKE/poster.png" --expected-file "$SMOKE/expected.txt" \
  --json "$SMOKE/report.json" > "$SMOKE/check_stdout.txt" 2> "$EVID/smoke_check_standalone.log"
CHECK_EXIT=$?
echo "standalone_check_exit=$CHECK_EXIT"
cp "$SMOKE/report.json" "$EVID/smoke_report_standalone.json" 2>/dev/null || true
printf '%s' "$CHECK_EXIT" > "$EVID/standalone_check_exit.txt"
cat "$SMOKE/check_stdout.txt"

# serve: start, poll health + UI, stop. Log goes to smoke_serve2.log.
"$VTP" serve --host 127.0.0.1 --port 8792 > "$EVID/smoke_serve2.log" 2>&1 &
SERVEPID=$!
sleep 2
python3 - "$SMOKE" <<'PYEOF'
import json, sys, time, urllib.request, urllib.error
for _ in range(60):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8792/api/v1/health", timeout=5) as r:
            print("health_status=", r.status, json.loads(r.read()), sep="")
            break
    except (urllib.error.URLError, ConnectionError):
        time.sleep(0.5)
else:
    print("health_status= TIMEOUT")
    sys.exit(1)
with urllib.request.urlopen("http://127.0.0.1:8792/", timeout=10) as r:
    html = r.read().decode("utf-8")
    print("ui_status=", r.status, "has_textproof=", "TextProof" in html,
          "has_export_warning=", "可能包含敏感文字" in html, sep="")
PYEOF
echo "serve_probe_exit=$?"
kill $SERVEPID 2>/dev/null
wait $SERVEPID 2>/dev/null
echo "serve_exit=$?"

# verify-s0 in the installed layout: both defined exit-3 refusals.
"$VTP" verify-s0 > "$SMOKE/verify_s0_default.txt" 2>&1
echo "verify_s0_default_exit=$?"
"$VTP" verify-s0 --manifest "$W/tests/fixtures/s0/manifest.json" > "$SMOKE/verify_s0_manifest.txt" 2>&1
echo "verify_s0_manifest_exit=$?"
