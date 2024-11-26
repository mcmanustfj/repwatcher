from pathlib import Path

from invoke import task  # type: ignore


@task
def clean(c, bytecode=False, extra=""):
    patterns = ["dist/*.tar.gz", "dist/*.whl"]
    if bytecode:
        patterns.append("**/*.pyc")
    if extra:
        patterns.append(extra)
    print(patterns)
    # walk through directory and delete files matching pattern
    for pattern in patterns:
        for path in Path(".").rglob(pattern):
            path.unlink()


@task(clean)
def build(c):
    c.run("uv build")
