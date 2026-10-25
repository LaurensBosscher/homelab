#!/usr/bin/env python3
"""Exit 10 when a quadlet's running container is not the image in its unit."""

import pathlib
import subprocess
import sys


def podman(*args):
    return subprocess.run(
        ["podman", *args],
        text=True,
        capture_output=True,
        check=False,
    )


def norm_ref(ref):
    ref = ref.strip()
    for prefix in ("docker.io/library/", "docker.io/"):
        if ref.startswith(prefix):
            return ref[len(prefix) :]
    return ref


def norm_id(value):
    value = value.strip()
    prefix = "sha256:"
    if value.startswith(prefix):
        return value[len(prefix) :]
    return value


def quadlet(unit):
    text = pathlib.Path(f"/etc/containers/systemd/{unit}.container").read_text()
    desired = ""
    container = f"systemd-{unit}"
    for line in text.splitlines():
        if line.startswith("Image="):
            desired = line.split("=", 1)[1].strip()
        elif line.startswith("ContainerName="):
            container = line.split("=", 1)[1].strip()
    if not desired:
        raise SystemExit(f"{unit} quadlet has no Image=")
    return desired, container


def pull(unit):
    # A quadlet pull runs inside the service and Podman only extends
    # TimeoutStartSec for about 255s. This link is slower than that for
    # a fresh image, so pull here before systemd starts the unit.
    desired, _container = quadlet(unit)
    proc = subprocess.run(
        ["timeout", "20m", "podman", "pull", desired],
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        print(f"pulled {desired}")
        return 0
    local = podman("image", "inspect", "--format", "{{.Id}}", desired)
    if local.returncode == 0:
        print(f"{unit} pull failed; keeping local {desired}")
        return 0
    if proc.stdout:
        print(proc.stdout, file=sys.stderr)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode or 1


def main():
    args = sys.argv[1:]
    if args[:1] == ["pull"]:
        return pull(args[1])
    unit = args[0]
    desired, container = quadlet(unit)

    running = podman("inspect", "--format", "{{.ImageName}}\n{{.Image}}", container)
    if running.returncode != 0:
        err = f"{running.stderr}{running.stdout}"
        if "no such object" in err.lower() or "no such container" in err.lower():
            print(f"{unit} container {container} is absent, want {desired}")
            return 10
        print(err, file=sys.stderr)
        return 1

    image_name, image_id = running.stdout.strip().split("\n", 1)
    if norm_ref(image_name) != norm_ref(desired):
        print(f"{unit} running {image_name}, want {desired}")
        return 10

    local = podman("image", "inspect", "--format", "{{.Id}}", desired)
    if local.returncode == 0 and norm_id(local.stdout) != norm_id(image_id):
        print(f"{unit} image id for {desired} changed")
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
