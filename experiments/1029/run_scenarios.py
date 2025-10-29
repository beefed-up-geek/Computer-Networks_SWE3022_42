#!/usr/bin/env python3
"""
Automates baseline TCP Reno experiments for five scenarios described in the
assignment. Each scenario spins up a dedicated Mininet topology, runs iperf3
flows, samples congestion window statistics via ss(8), and stores raw logs plus
summary metrics under experiments/1029/.
"""

import json
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet

BASE_DIR = Path("/home/gty/Computer-Networks_SWE3022_42/experiments/1029")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def simple_net():
    net = Mininet(link=TCLink, controller=None, build=False)
    try:
        yield net
    finally:
        net.stop()


def sample_loop(host, log_path: Path, stop_event: threading.Event, interval: float = 0.5):
    """
    Poll ss(8) from the given host until stop_event is set, logging RTT/cwnd/retrans stats.
    """
    cmd = "ss -tin '( dport = :5201 )'"
    with log_path.open("w") as log_file:
        while not stop_event.is_set():
            timestamp = time.time()
            output = host.cmd(cmd)
            log_file.write(f"{timestamp:.6f}\n{output.strip()}\n--\n")
            log_file.flush()
            stop_event.wait(interval)
        # final sample after completion
        timestamp = time.time()
        output = host.cmd(cmd)
        log_file.write(f"{timestamp:.6f}\n{output.strip()}\n--\n")
        log_file.flush()


def run_iperf(
    host_client,
    host_server,
    duration,
    log_dir: Path,
    label="flow",
    monitor_host=None,
    monitor_log: Path | None = None,
    monitor_interval: float = 0.5,
):
    server_log = log_dir / f"{label}_server.log"
    client_log = log_dir / f"{label}_client.json"
    if server_log.exists():
        server_log.unlink()
    if client_log.exists():
        client_log.unlink()
    server = host_server.popen(f"iperf3 -s --one-off --logfile {server_log}")
    time.sleep(1.0)
    client = host_client.popen(
        f"iperf3 -c {host_server.IP()} -t {duration} -i 1 -J --logfile {client_log}"
    )
    monitor_thread = None
    stop_event = None
    if monitor_host is not None and monitor_log is not None:
        stop_event = threading.Event()
        monitor_thread = threading.Thread(
            target=sample_loop,
            args=(monitor_host, monitor_log, stop_event, monitor_interval),
            daemon=True,
        )
        monitor_thread.start()

    client.wait()
    if stop_event is not None:
        stop_event.set()
        monitor_thread.join()

    time.sleep(1.0)
    if server.poll() is None:
        server.terminate()
        server.wait()
    return client_log


def parse_iperf_json(json_path: Path):
    raw = json_path.read_text().strip()
    if "}\n{" in raw:
        raw = "{" + raw.split("}\n{")[-1]
    data = json.loads(raw)
    intervals = [
        {
            "start": iv["sum"]["start"],
            "end": iv["sum"]["end"],
            "bits_per_second": iv["sum"]["bits_per_second"],
            "retransmits": iv["streams"][0].get("retransmits", 0) if iv["streams"] else None,
        }
        for iv in data.get("intervals", [])
    ]
    end_sum = data.get("end", {}).get("sum_received") or data.get("end", {}).get("sum_sent") or {}
    return {
        "intervals": intervals,
        "average_bps": end_sum.get("bits_per_second"),
        "bytes": end_sum.get("bytes"),
        "seconds": end_sum.get("seconds"),
        "retransmits": end_sum.get("retransmits"),
    }


def scenario1():
    """
    Single Reno flow through a 10 Mbps bottleneck to illustrate slow start and AIMD.
    """
    name = "scenario1_basic_aimd"
    duration = 60
    log_dir = ensure_dir(BASE_DIR / name)
    with simple_net() as net:
        h1 = net.addHost("h1")
        h2 = net.addHost("h2")
        s1 = net.addSwitch("s1", failMode="standalone")
        net.addLink(h1, s1, bw=10, delay="30ms", max_queue_size=100)
        net.addLink(h2, s1, bw=10, delay="30ms", max_queue_size=100)
        net.start()

        client_json = run_iperf(
            h1,
            h2,
            duration,
            log_dir,
            monitor_host=h1,
            monitor_log=log_dir / "cwnd.log",
        )
    return {
        "scenario": name,
        "description": "Baseline AIMD over single bottleneck",
        "iperf": parse_iperf_json(client_json),
    }


def scenario2():
    """
    Lossy link (5% random loss) to demonstrate Reno treating all loss as congestion.
    """
    name = "scenario2_lossy_link"
    duration = 60
    log_dir = ensure_dir(BASE_DIR / name)
    with simple_net() as net:
        h1 = net.addHost("h1")
        h2 = net.addHost("h2")
        s1 = net.addSwitch("s1", failMode="standalone")
        net.addLink(h1, s1, bw=10, delay="20ms", loss=5, max_queue_size=100)
        net.addLink(h2, s1, bw=10, delay="20ms", loss=5, max_queue_size=100)
        net.start()

        client_json = run_iperf(
            h1,
            h2,
            duration,
            log_dir,
            monitor_host=h1,
            monitor_log=log_dir / "cwnd.log",
        )
    return {
        "scenario": name,
        "description": "Random loss (5%)",
        "iperf": parse_iperf_json(client_json),
    }


def scenario3():
    """
    High bandwidth-delay product path to highlight Reno's slow window growth.
    """
    name = "scenario3_high_bdp"
    duration = 90
    log_dir = ensure_dir(BASE_DIR / name)
    with simple_net() as net:
        h1 = net.addHost("h1")
        h2 = net.addHost("h2")
        s1 = net.addSwitch("s1", failMode="standalone")
        net.addLink(h1, s1, bw=100, delay="150ms", max_queue_size=2000)
        net.addLink(h2, s1, bw=100, delay="150ms", max_queue_size=2000)
        net.start()

        client_json = run_iperf(
            h1,
            h2,
            duration,
            log_dir,
            monitor_host=h1,
            monitor_log=log_dir / "cwnd.log",
            monitor_interval=0.75,
        )
    return {
        "scenario": name,
        "description": "High BDP path (100 Mbps, 150 ms RTT)",
        "iperf": parse_iperf_json(client_json),
    }


def scenario4():
    """
    Competing flows with different RTTs to expose RTT unfairness.
    """
    name = "scenario4_rtt_unfairness"
    duration = 60
    log_dir = ensure_dir(BASE_DIR / name)
    with simple_net() as net:
        h1 = net.addHost("h1")
        h2 = net.addHost("h2")
        h3 = net.addHost("h3")
        s1 = net.addSwitch("s1", failMode="standalone")
        net.addLink(h1, s1, bw=20, delay="10ms", max_queue_size=200)
        net.addLink(h3, s1, bw=20, delay="100ms", max_queue_size=200)
        net.addLink(h2, s1, bw=20, delay="10ms", max_queue_size=200)
        net.start()

        server1_log = log_dir / "server_h1.log"
        server2_log = log_dir / "server_h3.log"
        stop_h1 = threading.Event()
        stop_h3 = threading.Event()
        monitor_h1 = threading.Thread(
            target=sample_loop,
            args=(h1, log_dir / "h1_cwnd.log", stop_h1, 0.5),
            daemon=True,
        )
        monitor_h3 = threading.Thread(
            target=sample_loop,
            args=(h3, log_dir / "h3_cwnd.log", stop_h3, 0.5),
            daemon=True,
        )
        monitor_h1.start()
        monitor_h3.start()

        client1_log = log_dir / "h1_client.json"
        client2_log = log_dir / "h3_client.json"
        for path in (client1_log, client2_log, server1_log, server2_log):
            if path.exists():
                path.unlink()
        server1 = h2.popen(
            f"iperf3 -s --one-off --logfile {server1_log} -p 5201"
        )
        server2 = h2.popen(
            f"iperf3 -s --one-off --logfile {server2_log} -p 5202"
        )
        time.sleep(1.0)
        client1 = h1.popen(
            f"iperf3 -c {h2.IP()} -t {duration} -i 1 -J -p 5201 --logfile {client1_log}"
        )
        time.sleep(0.5)
        client2 = h3.popen(
            f"iperf3 -c {h2.IP()} -t {duration} -i 1 -J -p 5202 --logfile {client2_log}"
        )

        client1.wait()
        client2.wait()
        time.sleep(1.0)
        for server in (server1, server2):
            if server.poll() is None:
                server.terminate()
                server.wait()
        stop_h1.set()
        stop_h3.set()
        monitor_h1.join()
        monitor_h3.join()

    data1 = parse_iperf_json(client1_log)
    data2 = parse_iperf_json(client2_log)
    throughputs = [tp for tp in (data1["average_bps"], data2["average_bps"]) if tp]
    fairness = None
    if len(throughputs) == 2:
        fairness = (sum(throughputs) ** 2) / (2 * sum(tp ** 2 for tp in throughputs))
    return {
        "scenario": name,
        "description": "RTT unfairness (short vs long RTT flows)",
        "iperf": {"h1": data1, "h3": data2},
        "fairness_index": fairness,
    }


def scenario5():
    """
    Large queue (bufferbloat) inducing high latency; optional UDP burst commented out.
    """
    name = "scenario5_bufferbloat"
    duration = 60
    log_dir = ensure_dir(BASE_DIR / name)
    with simple_net() as net:
        h1 = net.addHost("h1")
        h2 = net.addHost("h2")
        s1 = net.addSwitch("s1", failMode="standalone")
        net.addLink(h1, s1, bw=10, delay="20ms", max_queue_size=2000)
        net.addLink(h2, s1, bw=10, delay="20ms", max_queue_size=2000)
        net.start()

        client_json = run_iperf(
            h1,
            h2,
            duration,
            log_dir,
            monitor_host=h1,
            monitor_log=log_dir / "cwnd.log",
        )

        # Optional UDP burst for queue build-up (disabled by default; uncomment if needed).
        # h1.cmd("iperf3 -u -c 10.0.0.2 -t 10 -b 8M -l 1200 >> {}/udp_burst.log 2>&1 &".format(log_dir))
    return {
        "scenario": name,
        "description": "Bufferbloat with oversized queue",
        "iperf": parse_iperf_json(client_json),
    }


def main():
    setLogLevel("warning")
    summaries = []
    for func in (scenario1, scenario2, scenario3, scenario4, scenario5):
        print(f"Running {func.__name__} ...")
        summary = func()
        summaries.append(summary)
        # flush incremental summary per scenario
        (BASE_DIR / f"{summary['scenario']}_summary.json").write_text(
            json.dumps(summary, indent=2)
        )
        print(f"Completed {summary['scenario']}")
    (BASE_DIR / "summary.json").write_text(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    main()
