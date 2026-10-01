import os
import shlex
import subprocess


def _split_options(options):
    if not options:
        return []
    return shlex.split(str(options), posix=False)


def run_modern_steamless(executable, target, options="", timeout=180):
    """Run a modern Steamless CLI against the target in-place.

    Returns a result dictionary instead of raising for normal Steamless failures.
    """
    executable = os.path.abspath(executable)
    target = os.path.abspath(target)
    output_path = target + ".unpacked.exe"

    if not os.path.isfile(executable):
        raise FileNotFoundError(executable)
    if not os.path.isfile(target):
        raise FileNotFoundError(target)

    if os.path.isfile(output_path):
        os.remove(output_path)

    args = [executable, *_split_options(options), target]
    completed = subprocess.run(
        args,
        cwd=os.path.dirname(executable),
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )

    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
        "output_path": output_path,
        "unpacked": os.path.isfile(output_path),
    }
