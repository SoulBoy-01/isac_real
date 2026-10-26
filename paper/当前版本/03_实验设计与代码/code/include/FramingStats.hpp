// =============================================================================
//  FramingStats.hpp  —  分帧统计计数器（header-only）
//
//  版本：v2（2026-10-23）
//  v2 相对 v1 的变更：
//    - 新增 on_resync()：M2b 专用的"退重同步"计数
//    - 输出行增加 resync 字段
//
//  设计原则：
//    1. 输出单行、固定字段顺序、纯 ASCII，便于 Excel / Python 解析
//    2. 不依赖 spdlog，用 std::printf（可替换为 LOG_G_INFO() ）
//    3. 报告节奏与上游 [RS] ok=... 保持一致（每 200 块）
// =============================================================================

#pragma once

#include <cstdint>
#include <cstdio>
#include <cinttypes>

namespace framing {

class Stats {
public:
    // ---- 事件 ----
    void on_block()              { ++blocks_total_; }

    /// 块被丢弃（M0 的 NoBoundary / M1 的 BadLength / M2a 的 BadCrc）
    void on_drop()               { ++framing_drop_; }

    /// ★ M2b 专用：CRC 失败但未丢块，改交下游重同步
    void on_resync()             { ++resync_count_; }

    void on_seq_gap()            { ++seq_gap_; }
    void on_misalign()           { ++misalign_events_; }
    void on_deliver(size_t n)    { bytes_delivered_ += static_cast<uint64_t>(n); }

    /// 从失步恢复时调用，用于统计平均恢复块数
    void on_recover(uint32_t blocks_used) {
        recover_blocks_sum_ += blocks_used;
        ++recover_count_;
    }

    // ---- 读取 ----
    uint64_t blocks_total()    const { return blocks_total_; }
    uint64_t framing_drop()    const { return framing_drop_; }
    uint64_t resync_count()    const { return resync_count_; }
    uint64_t seq_gap()         const { return seq_gap_; }
    uint64_t misalign_events() const { return misalign_events_; }
    uint64_t bytes_delivered() const { return bytes_delivered_; }

    /// 丢块率（含所有失败原因，不含 resync）
    double drop_ratio() const {
        const uint64_t d = blocks_total_ + framing_drop_;
        return d ? static_cast<double>(framing_drop_) / static_cast<double>(d) : 0.0;
    }

    /// 失步率（失步事件数 / 块数）— 本文档定义的主判据
    double misalign_ratio() const {
        return blocks_total_
             ? static_cast<double>(misalign_events_) / static_cast<double>(blocks_total_)
             : 0.0;
    }

    /// 平均恢复块数（无恢复事件时返回 0）
    double recover_avg() const {
        return recover_count_
             ? static_cast<double>(recover_blocks_sum_) / static_cast<double>(recover_count_)
             : 0.0;
    }

    // ---- 报告 ----

    /// 每 200 块自动打印一次（调用点：每次 on_block() 之后）
    void maybe_report() {
        if (blocks_total_ - last_report_blocks_ >= 200) {
            last_report_blocks_ = blocks_total_;
            report();
        }
    }

    /// 强制输出一次
    void report() const {
        std::printf(
            "[FRAMING] blocks=%" PRIu64
            " drop=%" PRIu64
            " drop_ratio=%.4f"
            " resync=%" PRIu64
            " gap=%" PRIu64
            " misalign=%" PRIu64
            " misalign_ratio=%.4f"
            " recover_avg=%.1f"
            " delivered=%" PRIu64 "\n",
            blocks_total_, framing_drop_, drop_ratio(),
            resync_count_, seq_gap_,
            misalign_events_, misalign_ratio(),
            recover_avg(), bytes_delivered_);
        std::fflush(stdout);
    }

    void reset() {
        blocks_total_ = framing_drop_ = resync_count_ = 0;
        seq_gap_ = misalign_events_ = bytes_delivered_ = 0;
        recover_blocks_sum_ = recover_count_ = 0;
        last_report_blocks_ = 0;
    }

private:
    uint64_t blocks_total_       = 0;
    uint64_t framing_drop_       = 0;
    uint64_t resync_count_       = 0;
    uint64_t seq_gap_            = 0;
    uint64_t misalign_events_    = 0;
    uint64_t bytes_delivered_    = 0;
    uint64_t recover_blocks_sum_ = 0;
    uint64_t recover_count_      = 0;
    uint64_t last_report_blocks_ = 0;
};

} // namespace framing
