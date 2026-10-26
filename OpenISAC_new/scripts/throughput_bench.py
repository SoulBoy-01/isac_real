#!/usr/bin/env python3
"""ISAC 吞吐量自动化批量测试。BS TX，UE RX，自动记录 BER。"""
import socket, time, sys, json, struct

TEST_RATES = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
PKT_SIZE, DURATION = 1024, 10
UDP_IN = ("127.0.0.1", 50000)
UDP_OUT = ("0.0.0.0", 50001)

def run_tx(rate_kbps):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    seq, start = 0, time.time()
    interval = PKT_SIZE * 8 / (rate_kbps * 1000)
    while time.time() - start < DURATION:
        sock.sendto(struct.pack(">I", seq) + b"\xA5" * (PKT_SIZE - 4), UDP_IN)
        seq += 1
        next_t = start + seq * interval
        if (d := next_t - time.time()) > 0: time.sleep(d)
    sock.close(); return seq

def run_rx(timeout_s=12):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(UDP_OUT); sock.settimeout(2.0)
    total = bad = 0; start = time.time()
    while time.time() - start < timeout_s:
        try: data, _ = sock.recvfrom(65536)
        except socket.timeout: continue
        total += len(data); bad += sum(1 for b in data[4:] if b != 0xA5)
    sock.close()
    rx_rate = total * 8 / max(time.time() - start, 0.1) / 1000 if total > 0 else 0
    return total, bad, bad / total * 100 if total > 0 else 100, rx_rate

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "tx":
        print(f"TX: rates={TEST_RATES} kbps  pkt={PKT_SIZE}B  dur={DURATION}s")
        for r in TEST_RATES:
            print(f">>> {r}k...", end=" ", flush=True)
            pkts = run_tx(r); print(f"sent={pkts}")
            time.sleep(4)
    elif mode == "rx":
        print(f"RX on {UDP_OUT[0]}:{UDP_OUT[1]}")
        print(f"{'Rate':>6s}  {'KB':>8s}  {'Bad':>8s}  {'BER':>10s}")
        print("-" * 40)
        for r in TEST_RATES:
            total, bad, ber, rx_rate = run_rx()
            print(f"{r:>4d}k  {total/1024:>7.0f}KB  {bad:>8d}  {ber:>9.4f}%")
            time.sleep(3)
