#!/usr/bin/env python3
"""Generate plots and a summary table for TCP Reno baseline experiments."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = BASE_DIR / "summary.json"


@dataclass
class ScenarioMeta:
    key: str
    title: str
    topology: str
    highlight: str
    cwnd_logs: Dict[str, Path]
    throughput_label: Dict[str, str]
    palette: Dict[str, str]


SCENARIOS: Dict[str, ScenarioMeta] = {
    "scenario1_basic_aimd": ScenarioMeta(
        key="scenario1_basic_aimd",
        title="Scenario 1 – Slow Start & AIMD",
        topology="h1—s1—h2 · bw=10 Mbps · delay=30 ms · queue=100",
        highlight="Slow start 이후 선형 증가, 손실 시 cwnd 절반 감소",
        cwnd_logs={"flow": BASE_DIR / "scenario1_basic_aimd" / "cwnd.log"},
        throughput_label={"flow": "Throughput"},
        palette={"flow": "tab:blue"},
    ),
    "scenario2_lossy_link": ScenarioMeta(
        key="scenario2_lossy_link",
        title="Scenario 2 – Random Loss Misinterpretation",
        topology="h1—s1—h2 · bw=10 Mbps · delay=20 ms · loss=5%",
        highlight="비혼잡 손실에도 Reno가 감속 → 평균 처리량 급락",
        cwnd_logs={"flow": BASE_DIR / "scenario2_lossy_link" / "cwnd.log"},
        throughput_label={"flow": "Throughput"},
        palette={"flow": "tab:red"},
    ),
    "scenario3_high_bdp": ScenarioMeta(
        key="scenario3_high_bdp",
        title="Scenario 3 – High BDP Path",
        topology="h1—s1—h2 · bw=100 Mbps · delay=150 ms · queue=2000",
        highlight="RTT↑ 환경에서 선형 증가 속도가 느려 파이프 미충족",
        cwnd_logs={"flow": BASE_DIR / "scenario3_high_bdp" / "cwnd.log"},
        throughput_label={"flow": "Throughput"},
        palette={"flow": "tab:green"},
    ),
    "scenario4_rtt_unfairness": ScenarioMeta(
        key="scenario4_rtt_unfairness",
        title="Scenario 4 – RTT Unfairness",
        topology="h1/h3—s1—h2 · (h1:10 ms, h3:100 ms) · bw=20 Mbps",
        highlight="짧은 RTT 흐름이 대역폭 대부분 획득, Jain 지수 0.93",
        cwnd_logs={
            "h1": BASE_DIR / "scenario4_rtt_unfairness" / "h1_cwnd.log",
            "h3": BASE_DIR / "scenario4_rtt_unfairness" / "h3_cwnd.log",
        },
        throughput_label={"h1": "h1→h2", "h3": "h3→h2"},
        palette={"h1": "tab:blue", "h3": "tab:orange"},
    ),
    "scenario5_bufferbloat": ScenarioMeta(
        key="scenario5_bufferbloat",
        title="Scenario 5 – Bufferbloat & Fast Recovery",
        topology="h1—s1—h2 · bw=10 Mbps · delay=20 ms · queue=2000",
        highlight="크게 부푼 큐로 RTT 급증, Fast Retransmit/Recovery 반복",
        cwnd_logs={"flow": BASE_DIR / "scenario5_bufferbloat" / "cwnd.log"},
        throughput_label={"flow": "Throughput"},
        palette={"flow": "tab:purple"},
    ),
}


class CwndSeries:
    def __init__(self, times: List[float], cwnd: List[float], rtt: List[Tuple[float, float]]):
        self.times = times
        self.cwnd = cwnd
        self.rtt = rtt  # list of (time, rtt_ms)


def parse_summary() -> Dict[str, dict]:
    data = json.loads(SUMMARY_PATH.read_text())
    return {entry["scenario"]: entry for entry in data}


def select_primary_port(entries: Dict[int, List[Tuple[float, float, Optional[float], Optional[int]]]]) -> int:
    best_port = None
    best_metric = -math.inf
    for port, samples in entries.items():
        last_bytes = next((value for *_rest, value in reversed(samples) if value is not None), 0)
        if last_bytes > best_metric:
            best_metric = last_bytes
            best_port = port
    if best_port is None:
        # fall back to the port with the longest sample list
        best_port = max(entries.keys(), key=lambda p: len(entries[p]))
    return best_port


def parse_cwnd_log(path: Path) -> CwndSeries:
    if not path.exists():
        return CwndSeries([], [], [])
    entries: Dict[int, List[Tuple[float, float, Optional[float], Optional[int]]]] = defaultdict(list)
    timestamp: Optional[float] = None
    current_port: Optional[int] = None
    number_re = re.compile(r"cwnd:(\d+\.?\d*)")
    rtt_re = re.compile(r"rtt:(\d+\.?\d*)")
    bytes_re = re.compile(r"bytes_sent:(\d+)")
    port_re = re.compile(r"(\d+\.\d+\.\d+\.\d+):(\d+)\s+(\d+\.\d+\.\d+\.\d+):(\d+)")

    with path.open() as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            if line == "--":
                current_port = None
                continue
            if line.replace(".", "").isdigit():
                try:
                    timestamp = float(line)
                except ValueError:
                    timestamp = None
                continue
            if line.startswith("ESTAB"):
                match = port_re.search(line)
                current_port = int(match.group(2)) if match else None
                continue
            if "cwnd:" in line and timestamp is not None and current_port is not None:
                cwnd_match = number_re.search(line)
                if not cwnd_match:
                    continue
                cwnd_value = float(cwnd_match.group(1))
                rtt_match = rtt_re.search(line)
                rtt_value = float(rtt_match.group(1)) if rtt_match else None
                bytes_match = bytes_re.search(line)
                bytes_value = int(bytes_match.group(1)) if bytes_match else None
                entries[current_port].append((timestamp, cwnd_value, rtt_value, bytes_value))

    if not entries:
        return CwndSeries([], [], [])

    port = select_primary_port(entries)
    samples = entries[port]
    if not samples:
        return CwndSeries([], [], [])

    base_time = samples[0][0]
    times = [sample[0] - base_time for sample in samples]
    cwnd = [sample[1] for sample in samples]
    rtt = [(sample[0] - base_time, sample[2]) for sample in samples if sample[2] is not None]
    return CwndSeries(times, cwnd, rtt)


def plot_single_flow(meta: ScenarioMeta, summary: dict, scenario_dir: Path) -> Tuple[float, Optional[int]]:
    intervals = summary["iperf"]["intervals"]
    times = [0.5 * (iv["start"] + iv["end"]) for iv in intervals]
    throughput = [iv["bits_per_second"] / 1e6 for iv in intervals]

    cwnd_series = parse_cwnd_log(meta.cwnd_logs["flow"])

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
    axes[0].plot(times, throughput, color=meta.palette["flow"], label="Throughput")
    axes[0].set_ylabel("Throughput (Mbps)")
    axes[0].set_title(meta.title)
    axes[0].grid(True, linestyle=":", alpha=0.4)

    axes[1].plot(cwnd_series.times, cwnd_series.cwnd, color="tab:orange", label="cwnd")
    axes[1].set_ylabel("cwnd (packets)")
    axes[1].set_xlabel("Time (s)")
    axes[1].grid(True, linestyle=":", alpha=0.4)

    if cwnd_series.rtt:
        rtt_times, rtt_values = zip(*[(t, v) for t, v in cwnd_series.rtt if v is not None])
        ax_rtt = axes[1].twinx()
        ax_rtt.plot(rtt_times, rtt_values, color="tab:green", alpha=0.35, label="RTT (ms)")
        ax_rtt.set_ylabel("RTT (ms)")
        ax_rtt.tick_params(axis="y", labelcolor="tab:green")
        lines, labels = axes[1].get_legend_handles_labels()
        r_lines, r_labels = ax_rtt.get_legend_handles_labels()
        axes[1].legend(lines + r_lines, labels + r_labels, loc="upper right")
    else:
        axes[1].legend(loc="upper right")

    fig.tight_layout()
    output_path = scenario_dir / f"{meta.key}.png"
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    avg_mbps = summary["iperf"].get("average_bps")
    retrans = summary["iperf"].get("retransmits")
    return (avg_mbps / 1e6 if avg_mbps else float("nan"), retrans)


def plot_dual_flow(meta: ScenarioMeta, summary: dict, scenario_dir: Path) -> Tuple[Tuple[float, float], Optional[float]]:
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 6))

    avg_values = {}
    for flow in ("h1", "h3"):
        flow_summary = summary["iperf"][flow]
        intervals = flow_summary.get("intervals", [])
        times = [0.5 * (iv["start"] + iv["end"]) for iv in intervals]
        throughput = [iv["bits_per_second"] / 1e6 for iv in intervals]
        label = meta.throughput_label[flow]
        axes[0].plot(times, throughput, label=label, color=meta.palette[flow])
        avg_bps = flow_summary.get("average_bps")
        avg_values[flow] = avg_bps / 1e6 if avg_bps else float("nan")

    axes[0].set_ylabel("Throughput (Mbps)")
    axes[0].set_title(meta.title)
    axes[0].legend(loc="upper right")
    axes[0].grid(True, linestyle=":", alpha=0.4)

    for flow in ("h1", "h3"):
        cwnd_series = parse_cwnd_log(meta.cwnd_logs[flow])
        axes[1].plot(
            cwnd_series.times,
            cwnd_series.cwnd,
            label=f"{flow} cwnd",
            color=meta.palette[flow],
        )

    axes[1].set_ylabel("cwnd (packets)")
    axes[1].set_xlabel("Time (s)")
    axes[1].legend(loc="upper right")
    axes[1].grid(True, linestyle=":", alpha=0.4)

    fig.tight_layout()
    output_path = scenario_dir / f"{meta.key}.png"
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    fairness = summary.get("fairness_index")
    return (avg_values["h1"], avg_values["h3"]), fairness


def main() -> None:
    summary_by_key = parse_summary()
    rows: List[str] = []
    rows.append("| 시나리오 | 링크 조건 | 평균 처리량 (Mbps) | 관찰 포인트 |")
    rows.append("| --- | --- | --- | --- |")

    for key, meta in SCENARIOS.items():
        scenario_dir = BASE_DIR / key
        scenario_dir.mkdir(exist_ok=True)
        summary = summary_by_key[key]

        if key == "scenario4_rtt_unfairness":
            (avg_h1, avg_h3), fairness = plot_dual_flow(meta, summary, BASE_DIR)
            throughput_text = f"h1: {avg_h1:.2f} / h3: {avg_h3:.2f} (Jain {fairness:.2f})"
        else:
            avg_mbps, _ = plot_single_flow(meta, summary, BASE_DIR)
            throughput_text = f"{avg_mbps:.2f}"

        rows.append(
            f"| {meta.title} | {meta.topology} | {throughput_text} | {meta.highlight} |"
        )

    table_path = BASE_DIR / "metrics_table.md"
    table_path.write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
