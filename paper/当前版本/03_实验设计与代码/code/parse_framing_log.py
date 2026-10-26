#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_framing_log.py — D1/D2/D3 实验日志解析与指标计算

用途
----
从设备端 stdout 日志中解析 [FRAMING] 行，计算论文所需的全部指标，
并导出为 CSV，供后续作图与填表。

支持的日志格式
--------------
新的（FramingStats v2）：
    [FRAMING] blocks=12000 drop=3 drop_ratio=0.0003 resync=0 gap=1 \
              misalign=2 misalign_ratio=0.0002 recover_avg=8.5 delivered=11776000

旧的（只有部分字段，缺字段自动填 0）：
    [FRAMING] blocks=1000 drop=0 gap=0 misalign=0

也兼容上游的 RS 日志（用于交叉核对）：
    [RS] ok=200 fail=0 fail_rate=0.0000%

用法
----
  # 单个日志
  python parse_framing_log.py run_D2_M1_RSoff.log

  # 批量（按文件名自动提取 mode / rs 状态）
  python parse_framing_log.py data/*.log -o summary.csv

  # 指定元信息（文件名里没有时）
  python parse_framing_log.py run.log --mode prefix --rs off --snr 15

命名约定（批量模式会自动识别）
------------------------------
  推荐：run_<日期>_<模式>_RS<on|off>_<衰减>dB.log
  例：  run_1024_M2b_RSoff_15dB.log
        run_1024_M1_RSon_0dB.log

  识别规则：
    模式：none / m0 / prefix / m1 / m2a / prefix_crc_drop / m2b /
          prefix_crc_resync / chunked / m3
    RS  ：RSon / RSoff / rs_on / rs_off
    衰减：<数字>dB / atten<数字>

产出
----
  stdout         人读的汇总表
  <out>.csv      机器读的明细（每次运行一行）

指标定义（依《实验前判定口径_固定版.md》）
----------------------------------------
  失步率       = misalign / blocks          ← 主判据
  丢块率       = drop / (blocks + drop)
  重同步率     = resync / blocks            ← 仅 M2b
  序号缺口率   = gap / blocks               ← 仅 M3
  平均恢复块数 = recover_avg
  有效投递字节 = delivered
"""

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------

RE_FRAMING = re.compile(r"\[FRAMING\]\s*(.*)$")

# 键值对：key=value（value 可为整数/浮点/百分数）
RE_KV = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(-?\d+(?:\.\d+)?%?)")

# 上游 RS 日志
RE_RS = re.compile(r"\[RS\]\s*ok=(\d+)\s+fail=(\d+)\s+fail_rate=([\d.]+)%")

# 模式识别
MODE_PATTERNS = [
    (re.compile(r"(?:^|[_\-. ])m0(?:$|[_\-. ])|none", re.I), "M0"),
    (re.compile(r"(?:^|[_\-. ])m2b(?:$|[_\-. ])|prefix_crc_resync|resync", re.I), "M2b"),
    (re.compile(r"(?:^|[_\-. ])m2a(?:$|[_\-. ])|prefix_crc_drop|crc_drop", re.I), "M2a"),
    (re.compile(r"(?:^|[_\-. ])m1(?:$|[_\-. ])|(?<!crc_)prefix(?!_crc)", re.I), "M1"),
    (re.compile(r"(?:^|[_\-. ])m3(?:$|[_\-. ])|chunked|chunk", re.I), "M3"),
]

MODE_ORDER = {"M0": 0, "M1": 1, "M2a": 2, "M2b": 3, "M3": 4}


@dataclass
class FramingSample:
    """一条 [FRAMING] 日志的内容（累计值，非增量）"""
    blocks: int = 0
    drop: int = 0
    drop_ratio: float = 0.0
    resync: int = 0
    gap: int = 0
    misalign: int = 0
    misalign_ratio: float = 0.0
    recover_avg: float = 0.0
    delivered: int = 0
    raw: str = ""


@dataclass
class RunResult:
    """一次实验运行的汇总"""
    file: str = ""
    mode: str = ""
    rs: str = ""
    snr_db: Optional[float] = None
    # 取最后一次 FRAMING 报告（累计值最大）
    blocks: int = 0
    drop: int = 0
    resync: int = 0
    gap: int = 0
    misalign: int = 0
    delivered: int = 0
    recover_avg: float = 0.0
    # 计算得到的指标
    misalign_rate: float = 0.0
    drop_rate: float = 0.0
    resync_rate: float = 0.0
    gap_rate: float = 0.0
    # 交叉核对
    rs_ok: int = 0
    rs_fail: int = 0
    n_reports: int = 0
    warnings: list = field(default_factory=list)


def parse_value(token: str):
    """'123' -> int, '0.0003' -> float, '12.5%' -> 12.5"""
    if token.endswith("%"):
        return float(token[:-1])
    if "." in token:
        return float(token)
    return int(token)


def parse_framing_line(line: str) -> Optional[FramingSample]:
    m = RE_FRAMING.search(line)
    if not m:
        return None
    body = m.group(1)
    s = FramingSample(raw=line.strip())
    found = 0
    for key, val in RE_KV.findall(body):
        k = key.lower()
        try:
            v = parse_value(val)
        except ValueError:
            continue
        if k == "blocks":
            s.blocks = int(v); found += 1
        elif k == "drop":
            s.drop = int(v); found += 1
        elif k == "drop_ratio":
            s.drop_ratio = float(v); found += 1
        elif k == "resync":
            s.resync = int(v); found += 1
        elif k == "gap":
            s.gap = int(v); found += 1
        elif k == "misalign":
            s.misalign = int(v); found += 1
        elif k == "misalign_ratio":
            s.misalign_ratio = float(v); found += 1
        elif k == "recover_avg":
            s.recover_avg = float(v); found += 1
        elif k == "delivered":
            s.delivered = int(v); found += 1
    return s if found else None


def guess_mode(name: str) -> str:
    for pat, tag in MODE_PATTERNS:
        if pat.search(name):
            return tag
    return ""


def guess_rs(name: str) -> str:
    if re.search(r"rs[_\-. ]?on", name, re.I):
        return "on"
    if re.search(r"rs[_\-. ]?off", name, re.I):
        return "off"
    return ""


def guess_snr(name: str) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*dB", name, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"atten(\d+(?:\.\d+)?)", name, re.I)
    if m:
        return -float(m.group(1))     # 衰减记为负的 SNR 偏移
    return None


def analyze(path: str, mode="", rs="", snr=None) -> RunResult:
    res = RunResult(file=os.path.basename(path))
    res.mode = mode or guess_mode(res.file)
    res.rs = rs or guess_rs(res.file)
    res.snr_db = snr if snr is not None else guess_snr(res.file)

    samples = []
    last_rs = None

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = parse_framing_line(line)
            if s:
                samples.append(s)
                continue
            m = RE_RS.search(line)
            if m:
                last_rs = (int(m.group(1)), int(m.group(2)))

    res.n_reports = len(samples)

    if not samples:
        res.warnings.append("未找到 [FRAMING] 行")
        # 仍尝试保留 RS 统计
        if last_rs:
            res.rs_ok, res.rs_fail = last_rs
        return res

    # 取累计值最大的那条（即最后一条）
    final = max(samples, key=lambda x: x.blocks)

    # 一致性检查：中途 blocks 若回退，说明进程重启过
    max_blocks = final.blocks
    monotonic = all(
        samples[i].blocks <= samples[i + 1].blocks
        for i in range(len(samples) - 1)
    )
    if not monotonic:
        res.warnings.append("blocks 计数非单调，可能进程重启过（已取最大值）")

    res.blocks = final.blocks
    res.drop = final.drop
    res.resync = final.resync
    res.gap = final.gap
    res.misalign = final.misalign
    res.delivered = final.delivered
    res.recover_avg = final.recover_avg

    # 指标换算
    if res.blocks > 0:
        res.misalign_rate = res.misalign / res.blocks
        res.resync_rate = res.resync / res.blocks
        res.gap_rate = res.gap / res.blocks
    denom = res.blocks + res.drop
    res.drop_rate = (res.drop / denom) if denom > 0 else 0.0

    if last_rs:
        res.rs_ok, res.rs_fail = last_rs

    # 与日志内的 *_ratio 字段交叉核对
    if final.misalign_ratio and abs(res.misalign_rate - final.misalign_ratio) > 1e-6:
        res.warnings.append(
            f"misalign_ratio 自报 {final.misalign_ratio:.6f} "
            f"与计算 {res.misalign_rate:.6f} 不一致")

    return res


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "file", "mode", "rs", "snr_db",
    "blocks", "drop", "resync", "gap", "misalign", "delivered", "recover_avg",
    "misalign_rate", "drop_rate", "resync_rate", "gap_rate",
    "rs_ok", "rs_fail", "n_reports", "warnings",
]


def result_to_row(r: RunResult) -> dict:
    d = asdict(r)
    d["warnings"] = "; ".join(r.warnings)
    return d


def print_summary(results):
    """按 (mode, rs, snr) 排序，打印人读表格"""
    results = sorted(
        results,
        key=lambda r: (MODE_ORDER.get(r.mode, 9), r.rs or "", r.snr_db or 0)
    )

    hdr = (f"{'file':<36}{'mode':<6}{'RS':<5}{'SNR':>6}"
           f"{'blocks':>9}{'misalign':>10}{'mis_rate':>11}{'drop%':>9}"
           f"{'resync':>8}{'gap':>6}")
    print(hdr)
    print("-" * len(hdr))
    for r in results:
        snr = f"{r.snr_db:g}" if r.snr_db is not None else "-"
        print(f"{r.file[:35]:<36}{r.mode or '?':<6}{r.rs or '?':<5}{snr:>6}"
              f"{r.blocks:>9}{r.misalign:>10}{r.misalign_rate*100:>10.4f}%"
              f"{r.drop_rate*100:>8.3f}%{r.resync:>8}{r.gap:>6}")

    # 警告汇总
    warn = [r for r in results if r.warnings]
    if warn:
        print("\n[警告]")
        for r in warn:
            print(f"  {r.file}: {'; '.join(r.warnings)}")

    # 若同一 (mode, rs) 有多次重复，报离散度
    print("\n[重复性]")
    groups = {}
    for r in results:
        key = (r.mode, r.rs)
        groups.setdefault(key, []).append(r.misalign_rate)

    any_group = False
    for (mode, rs), vals in sorted(groups.items(),
                                   key=lambda kv: MODE_ORDER.get(kv[0][0], 9)):
        if len(vals) < 2:
            continue
        any_group = True
        mean = sum(vals) / len(vals)
        spread = max(vals) - min(vals) if len(vals) > 1 else 0
        cv = (spread / mean) if mean > 0 else 0
        flag = "  <-- 离散度偏高，建议补跑" if cv > 0.5 else ""
        print(f"  {mode or '?'}/{rs or '?'}: n={len(vals)} "
              f"mean={mean*100:.4f}% range={spread*100:.4f}%"
              f" CV={cv:.2f}{flag}")

    if not any_group:
        print("  （无重复组）")


def main():
    ap = argparse.ArgumentParser(
        description="解析 [FRAMING] 日志并计算论文指标")
    ap.add_argument("files", nargs="+", help="日志文件（支持通配符）")
    ap.add_argument("-o", "--out", default="framing_summary.csv",
                    help="输出 CSV（默认 framing_summary.csv）")
    ap.add_argument("--mode", default="", help="强制指定模式（M0/M1/M2a/M2b/M3）")
    ap.add_argument("--rs", default="", help="强制指定 RS 状态（on/off）")
    ap.add_argument("--snr", type=float, default=None,
                    help="强制指定 SNR/衰减档位（dB）")
    ap.add_argument("-q", "--quiet", action="store_true", help="只写 CSV，不打印")
    args = ap.parse_args()

    # 展开通配符
    import glob
    paths = []
    for f in args.files:
        matched = glob.glob(f)
        paths.extend(matched if matched else ([f] if os.path.exists(f) else []))

    if not paths:
        print("[error] 未找到任何日志文件", file=sys.stderr)
        dirs = os.path.dirname(args.files[0]) or "."
        if os.path.isdir(dirs):
            print(f"        目录 {dirs} 下现有文件：", file=sys.stderr)
            for n in sorted(os.listdir(dirs))[:20]:
                print(f"          {n}", file=sys.stderr)
        sys.exit(1)

    results = [analyze(p, args.mode, args.rs, args.snr) for p in paths]

    if not args.quiet:
        print_summary(results)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in results:
            w.writerow(result_to_row(r))

    if not args.quiet:
        print(f"\n已写出: {args.out}  （{len(results)} 行）")

    # 退出码：若有未找到 FRAMING 的文件，返回 2
    if any("未找到 [FRAMING] 行" in r.warnings for r in results):
        sys.exit(2)


if __name__ == "__main__":
    main()
