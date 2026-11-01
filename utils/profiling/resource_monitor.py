# utils/profiling/resource_monitor.py


import csv
import os
import threading
import time
from dataclasses import dataclass, asdict
from typing import List, Optional

import psutil


@dataclass
class Sample:
    t_sec: float
    cpu_percent: float
    rss_bytes: int


class ResourceMonitor:
    """Background sampler for process CPU% and memory usage (RSS)."""

    def __init__(self, interval_sec: float = 0.5, out_csv_path: Optional[str] = None):
        self.interval = interval_sec
        self.out_csv_path = out_csv_path
        self._proc = psutil.Process(os.getpid())
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._t0: float = 0.0
        self._samples: List[Sample] = []

    def start(self) -> None:
        self._t0 = time.perf_counter()
        # Warm up psutil cpu_percent baseline
        self._proc.cpu_percent(interval=None)
        self._thread = threading.Thread(target=self._run, name="ResourceMonitor", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            cpu = self._proc.cpu_percent(interval=None)
            mem = self._proc.memory_info().rss
            ts = time.perf_counter() - self._t0
            self._samples.append(Sample(ts, cpu, mem))
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join()
        if self.out_csv_path:
            self._write_csv(self.out_csv_path)

    def _write_csv(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["t_sec", "cpu_percent", "rss_bytes"])
            w.writeheader()
            for s in self._samples:
                w.writerow(asdict(s))

    @property
    def samples(self) -> List[Sample]:
        return self._samples
