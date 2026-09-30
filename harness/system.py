"""Device specs, offline check and memory measurement for the evidence records."""
import ctypes
import datetime as dt
import os
import platform
import shutil
import socket
import subprocess
import sys

from .config import ROOT


def internet_reachable(timeout=3):
    """True if any well-known public host answers. Used to prove the offline runs were offline."""
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53), ("github.com", 443)):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def total_ram_gb():
    try:
        if sys.platform == "win32":
            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.ullTotalPhys / 1e9, 1), round(m.ullAvailPhys / 1e9, 1)
        if sys.platform == "darwin":
            total = int(_run(["sysctl", "-n", "hw.memsize"]) or 0)
            return round(total / 1e9, 1), None
        info = dict(l.split(":", 1) for l in open("/proc/meminfo") if ":" in l)
        kb = lambda k: int(info[k].strip().split()[0])  # noqa: E731
        return round(kb("MemTotal") * 1024 / 1e9, 1), round(kb("MemAvailable") * 1024 / 1e9, 1)
    except Exception:  # noqa: BLE001
        return None, None


def gpus():
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    if out:
        return [l.strip() for l in out.splitlines()]
    if sys.platform == "win32":
        out = _run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }"])
        return [l.strip() for l in out.splitlines() if l.strip()]
    if sys.platform == "darwin":
        return [platform.processor() + " (unified memory)"]
    return []


def cpu_name():
    if sys.platform == "win32":
        out = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"])
        return out or platform.processor()
    if sys.platform == "darwin":
        return _run(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor()
    for l in open("/proc/cpuinfo") if os.path.exists("/proc/cpuinfo") else []:
        if l.startswith("model name"):
            return l.split(":", 1)[1].strip()
    return platform.processor()


def ollama_process_memory_gb():
    """Resident memory of all Ollama processes (server + model runner)."""
    # Recent Ollama builds run the model in a child process named llama-server.
    if sys.platform == "win32":
        out = _run(["powershell", "-NoProfile", "-Command",
                    "(Get-Process | Where-Object { $_.ProcessName -like 'ollama*' -or $_.ProcessName -like 'llama-server*' } | Measure-Object WorkingSet64 -Sum).Sum"])
        try:
            return round(int(out) / 1e9, 2)
        except ValueError:
            return None
    out = _run(["ps", "-C", "ollama", "-o", "rss="]) or _run(["sh", "-c", "ps -axo rss,comm | grep -iE 'ollama|llama-server' | awk '{s+=$1} END {print s}'"])
    try:
        return round(sum(int(x) for x in out.split()) * 1024 / 1e9, 2)
    except ValueError:
        return None


def device_specs():
    total, avail = total_ram_gb()
    du = shutil.disk_usage(ROOT)
    return {
        "captured_at": dt.datetime.now().isoformat(timespec="seconds"),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "machine": platform.machine(),
        "cpu": cpu_name(),
        "cpu_threads": os.cpu_count(),
        "ram_total_gb": total,
        "ram_available_gb": avail,
        "gpus": gpus(),
        "disk_free_gb": round(du.free / 1e9, 1),
        "python": sys.version.split()[0],
        "ollama_cli": _run(["ollama", "--version"]),
    }
