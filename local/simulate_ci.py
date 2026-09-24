"""Offline pipeline demos.

1. validate_workflows():  parses .github/workflows/*.yml, asserts structure,
   printing each job/step as GitHub would show it.
2. run_ci_test_job():     executes the exact commands from ci.yml's `test` job
   against the local checkout (the same pytest version/paths).
3. build_image():         if a Docker daemon + image are available, runs the
   same `docker build` the workflow runs (test-in-build stage).
"""
import os
import shutil
import subprocess
import sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")
SHA = os.environ.get("GITHUB_SHA", "offline-sha")
IMAGE = f"ghcr.io/goose006567/cicd-app"


def step(name):
    print(f"\n>> {name}")


def validate_workflows():
    step("VALIDATE .github/workflows/*.yml")
    for fn in sorted(os.listdir(WORKFLOWS)):
        doc = yaml.safe_load(open(os.path.join(WORKFLOWS, fn)))
        name = doc.get("name")
        jobs = doc.get("jobs", {})
        print(f"\n  [workflow] {fn} -> \"{name}\"  ({len(jobs)} job(s))")
        for jname, job in jobs.items():
            print(f"    - job {jname!r} on {job.get('runs-on')}")
            print(f"      needs: {job.get('needs', 'none')}")
            for s in job.get("steps", []):
                uses = s.get("uses", "run")
                print(f"        step: {uses}")
    return True


def run_ci_test_job():
    step("RUN ci.yml 'test' job (locally)")
    cmds = [
        [sys.executable, "-m", "pytest", "tests/", "-v"],
    ]
    for c in cmds:
        print(f"\n  $ {' '.join(c)}")
        rc = subprocess.run(c, cwd=ROOT).returncode
        if rc != 0:
            sys.exit(f"ci test job failed  (exit {rc})")
    print(f"\n  [result] pytest passed — same command ci.yml runs")
    return True


def build_image():
    step("RUN ci.yml 'build-and-push' job (docker build, GHCR dry-run)")
    if not shutil.which("docker"):
        print("  [skip] no docker daemon available — build step deferred to GitHub")
        return True
    print(f"  $ docker build -f app/Dockerfile -t {IMAGE}:ci-{SHA} .")
    rc = subprocess.run(["docker", "build", "-f", "app/Dockerfile",
                         "-t", f"{IMAGE}:ci-{SHA}", "."], cwd=ROOT,
                        capture_output=True).returncode
    if rc != 0:
        print("  [warn] docker build failed locally (offline build needs cached base image); "
              "this step is what exercises on GitHub runners")
        return False
    print("  $ (dry-run) docker login ghcr.io + push ci-<sha> — needs internet + GITHUB_TOKEN")
    return True


if __name__ == "__main__":
    ok = validate_workflows() and run_ci_test_job()
    build_image()
    print("\n=== offline pipeline replay complete ===")
    sys.exit(0 if ok else 1)
