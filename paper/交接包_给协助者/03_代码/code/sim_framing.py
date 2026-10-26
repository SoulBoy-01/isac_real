#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sim_framing.py — 五模式分帧的离线蒙特卡洛模拟（v2）

五种模式：
    none               M0  无边界信息
    prefix             M1  裸长度字段
    prefix_crc_drop    M2a 长度+CRC，CRC 失败丢块
    prefix_crc_resync  M2b 长度+CRC，CRC 失败交下游重同步
    chunked            M3  定长分块

主判据（依《实验前判定口径_固定版.md》）：
    失步率 = 失步事件 / 块数    ← 主判据
    投递率 = 有效字节 / 总字节  ← 辅助
    丢块率                      ← 辅助
    重同步次数                  ← 仅 M2b

运行：
    python sim_framing.py
    python sim_framing.py --trials 50 --packets 500
"""

import argparse
import csv
import os

import numpy as np

# ---------------------------------------------------------------------------
# 参数（与 Framing.hpp 保持一致）
# ---------------------------------------------------------------------------

K_PREFIX_LEN = 2
K_CRC_LEN = 2
K_PREFIX_CRC_HEAD = K_PREFIX_LEN + K_CRC_LEN      # 4
K_CHUNK_SIZE = 1024
K_CHUNK_HEAD = 2
K_CHUNK_PAYLOAD = K_CHUNK_SIZE - K_CHUNK_HEAD     # 1022
K_MISALIGN_RUN = 3

START_CODE = b"\x00\x00\x00\x01"

PAYLOAD_LEN = 1024
RS_K = 223
RS_N = 255

MODES = ["none", "prefix", "prefix_crc_drop", "prefix_crc_resync", "chunked"]

LABEL = {
    "none":              "M0 无锚点",
    "prefix":            "M1 裸前缀",
    "prefix_crc_drop":   "M2a CRC+丢块",
    "prefix_crc_resync": "M2b CRC+重同步",
    "chunked":           "M3 定长分片",
}

COLOR = {
    "none":              "#c0392b",
    "prefix":            "#e67e22",
    "prefix_crc_drop":   "#8e44ad",
    "prefix_crc_resync": "#2980b9",
    "chunked":           "#27ae60",
}

MARKER = {
    "none":              "o",
    "prefix":            "s",
    "prefix_crc_drop":   "v",
    "prefix_crc_resync": "^",
    "chunked":           "D",
}

# ---------------------------------------------------------------------------
# 数据构造
# ---------------------------------------------------------------------------


def make_h264_like_stream(n_packets, payload_len, rng):
    """造一段"像 H.264"的字节流：每 ~512 字节插一个起始码"""
    total = n_packets * payload_len
    buf = rng.integers(0, 256, size=total, dtype=np.uint8)
    for i in range(total - 4):
        if buf[i] == 0 and buf[i + 1] == 0 and buf[i + 2] == 0:
            buf[i + 2] = 1
    for pos in range(0, total - 4, 512):
        buf[pos:pos + 4] = [0, 0, 0, 1]
    return buf


def crc16_ccitt(data):
    crc = 0xFFFF
    for b in data:
        crc ^= int(b) << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


def build_frames(stream, payload_len, mode, rng):
    """返回 (frames, 每帧真实载荷长度)"""
    frames = []
    real_lens = []

    if mode == "chunked":
        n_chunks = (len(stream) + K_CHUNK_PAYLOAD - 1) // K_CHUNK_PAYLOAD
        for i in range(n_chunks):
            off = i * K_CHUNK_PAYLOAD
            chunk = stream[off:off + K_CHUNK_PAYLOAD]
            real_lens.append(len(chunk))
            if len(chunk) < K_CHUNK_PAYLOAD:
                chunk = np.concatenate(
                    [chunk, np.zeros(K_CHUNK_PAYLOAD - len(chunk), dtype=np.uint8)]
                )
            head = np.array([(i >> 8) & 0xFF, i & 0xFF], dtype=np.uint8)
            frames.append(np.concatenate([head, chunk]))
        return frames, real_lens

    n_packets = len(stream) // payload_len
    for i in range(n_packets):
        payload = stream[i * payload_len:(i + 1) * payload_len]
        real_lens.append(len(payload))
        L = len(payload)

        if mode == "none":
            frames.append(payload.copy())
        elif mode == "prefix":
            head = np.array([(L >> 8) & 0xFF, L & 0xFF], dtype=np.uint8)
            frames.append(np.concatenate([head, payload]))
        elif mode in ("prefix_crc_drop", "prefix_crc_resync"):
            head = np.array([(L >> 8) & 0xFF, L & 0xFF], dtype=np.uint8)
            crc = crc16_ccitt(head)
            crchead = np.array([(crc >> 8) & 0xFF, crc & 0xFF], dtype=np.uint8)
            frames.append(np.concatenate([head, crchead, payload]))
        else:
            raise ValueError(mode)
    return frames, real_lens


# ---------------------------------------------------------------------------
# 误码与解帧
# ---------------------------------------------------------------------------


def inject_bit_errors(frame, p, rng):
    if p <= 0:
        return frame
    n_bits = len(frame) * 8
    n_err = rng.binomial(n_bits, p)
    if n_err == 0:
        return frame
    out = frame.copy()
    for _ in range(n_err):
        bit = rng.integers(0, n_bits)
        out[bit // 8] ^= np.uint8(1 << (bit % 8))
    return out


def has_start_code(arr):
    n = len(arr)
    if n < 4:
        return False
    for k in range(n - 3):
        if arr[k] == 0 and arr[k + 1] == 0 and arr[k + 2] == 0 and arr[k + 3] == 1:
            return True
    return False


def decode(frame, mode, expect_len, last_seq, has_prev):
    """返回 (status, payload, seq, seq_gap)

    status: ok / bad_length / bad_crc / resync / no_boundary
    """
    if mode == "none":
        if expect_len == 0 or expect_len > len(frame):
            return "bad_length", None, 0, False
        return "ok", frame[:expect_len], 0, False

    if mode == "prefix":
        if len(frame) < K_PREFIX_LEN:
            return "bad_length", None, 0, False
        L = (int(frame[0]) << 8) | int(frame[1])
        if L == 0 or L + K_PREFIX_LEN > len(frame):
            return "bad_length", None, 0, False
        return "ok", frame[K_PREFIX_LEN:K_PREFIX_LEN + L], 0, False

    if mode in ("prefix_crc_drop", "prefix_crc_resync"):
        if len(frame) < K_PREFIX_CRC_HEAD:
            return "bad_length", None, 0, False
        want = (int(frame[2]) << 8) | int(frame[3])
        calc = crc16_ccitt(frame[0:2])
        if want != calc:
            if mode == "prefix_crc_resync":
                # ★ M2b：不丢块，整块交给下游（含保护头）
                return "resync", frame[K_PREFIX_CRC_HEAD:], 0, False
            return "bad_crc", None, 0, False
        L = (int(frame[0]) << 8) | int(frame[1])
        if L == 0 or L + K_PREFIX_CRC_HEAD > len(frame):
            return "bad_length", None, 0, False
        return "ok", frame[K_PREFIX_CRC_HEAD:K_PREFIX_CRC_HEAD + L], 0, False

    if mode == "chunked":
        if len(frame) < K_CHUNK_SIZE:
            return "bad_length", None, 0, False
        seq = (int(frame[0]) << 8) | int(frame[1])
        gap = has_prev and ((seq - last_seq) & 0xFFFF) != 1
        return "ok", frame[K_CHUNK_HEAD:K_CHUNK_HEAD + K_CHUNK_PAYLOAD], seq, gap

    raise ValueError(mode)


# ---------------------------------------------------------------------------
# 单次模拟
# ---------------------------------------------------------------------------


def run_one(mode, p, n_packets, rng, expect_len_mismatch=True):
    stream = make_h264_like_stream(n_packets, PAYLOAD_LEN, rng)
    frames, real_lens = build_frames(stream, PAYLOAD_LEN, mode, rng)

    n_blocks = len(frames)
    n_drop = 0
    n_resync = 0
    n_seq_gap = 0
    n_misalign = 0
    bad_run = 0
    delivered_bytes = 0
    total_bytes = sum(real_lens)

    last_seq = 0
    has_prev = False

    rs_len = int(np.ceil((PAYLOAD_LEN + K_PREFIX_LEN) / RS_K)) * RS_N
    expect = rs_len if expect_len_mismatch else PAYLOAD_LEN

    for fr in frames:
        bad = inject_bit_errors(fr, p, rng)
        status, payload, seq, gap = decode(bad, mode, expect, last_seq, has_prev)

        ok = status in ("ok", "resync")
        if status == "resync":
            n_resync += 1
        if status in ("bad_crc", "bad_length"):
            n_drop += 1
        if gap:
            n_seq_gap += 1
        if mode == "chunked" and status == "ok":
            last_seq = seq
            has_prev = True

        # 失步判定：投递内容中是否含起始码（resync 也算投递）
        hsc = False
        if ok and payload is not None and len(payload) > 0:
            hsc = has_start_code(payload)
            delivered_bytes += len(payload)
        if hsc:
            bad_run = 0
        else:
            bad_run += 1
            if bad_run == K_MISALIGN_RUN:
                n_misalign += 1

    delivered_bytes = min(delivered_bytes, total_bytes * 2)  # 防越界
    delivered_ratio = min(1.0, delivered_bytes / total_bytes) if total_bytes else 0.0

    return {
        "mode": mode,
        "p": p,
        "blocks": n_blocks,
        "drop": n_drop,
        "drop_rate": n_drop / n_blocks if n_blocks else 0.0,
        "resync": n_resync,
        "seq_gap": n_seq_gap,
        "misalign": n_misalign,
        "misalign_rate": n_misalign / n_blocks if n_blocks else 0.0,
        "delivered_ratio": delivered_ratio,
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--packets", type=int, default=400)
    ap.add_argument("--out", type=str, default="sim_framing.png")
    ap.add_argument("--seed", type=int, default=20261023)
    args = ap.parse_args()

    ps = [0, 1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]

    rng = np.random.default_rng(args.seed)
    rows = []

    print(f"trials={args.trials} packets={args.packets}")
    hdr = f"{'mode':<20}{'p':>10}{'drop_rate':>12}{'resync':>10}{'misalign':>12}{'delivered':>12}"
    print(hdr)
    print("-" * len(hdr))

    for mode in MODES:
        for p in ps:
            acc = [run_one(mode, p, args.packets, rng) for _ in range(args.trials)]
            numeric_keys = [k for k in acc[0] if k != "mode"]
            agg = {k: float(np.mean([a[k] for a in acc])) for k in numeric_keys}
            agg["mode"] = mode
            agg["p"] = p
            rows.append(agg)
            print(f"{mode:<20}{p:>10.0e}{agg['drop_rate']:>12.4f}"
                  f"{agg['resync']:>10.1f}{agg['misalign_rate']:>12.4f}"
                  f"{agg['delivered_ratio']:>12.4f}")

    csv_path = os.path.splitext(args.out)[0] + "_result.csv"
    keys = ["mode", "p", "blocks", "drop", "drop_rate", "resync",
            "seq_gap", "misalign", "misalign_rate", "delivered_ratio"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in keys})
    print(f"\nwritten: {csv_path}")

    # ---- 画图 ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm

        for cand in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
                     "Source Han Sans SC", "WenQuanYi Zen Hei", "DejaVu Sans"]:
            if cand in {f.name for f in fm.fontManager.ttflist}:
                matplotlib.rcParams["font.sans-serif"] = [cand, "DejaVu Sans"]
                break
        matplotlib.rcParams["axes.unicode_minus"] = False

        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=160)

        for mode in MODES:
            sub = [r for r in rows if r["mode"] == mode]
            xs = [max(r["p"], 1e-7) for r in sub]
            kw = dict(color=COLOR[mode], marker=MARKER[mode],
                      linewidth=1.5, markersize=5, label=LABEL[mode])
            axes[0].plot(xs, [r["misalign_rate"] for r in sub], **kw)
            axes[1].plot(xs, [r["delivered_ratio"] for r in sub], **kw)

        for ax, title, ylab in [
            (axes[0], "(a) 流级失步率（主判据）", "失步事件 / 块数"),
            (axes[1], "(b) 有效投递率（辅助）", "有效字节 / 总字节"),
        ]:
            ax.set_xscale("log")
            ax.set_xlabel("残余字节误码率 $p$")
            ax.set_ylabel(ylab)
            ax.set_title(title, fontsize=10)
            ax.grid(True, which="both", alpha=0.25, linewidth=0.6)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        axes[0].legend(fontsize=7.5, frameon=False, loc="upper left")
        fig.tight_layout()
        fig.savefig(args.out, bbox_inches="tight")
        print(f"written: {args.out}")
    except ImportError:
        print("matplotlib 未安装，跳过画图")


if __name__ == "__main__":
    main()
