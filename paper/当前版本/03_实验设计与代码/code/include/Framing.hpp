// =============================================================================
//  Framing.hpp  —  五模式分帧的纯函数实现（header-only，零依赖）
//
//  版本：v2（2026-10-23）
//  v2 相对 v1 的变更：
//    - M2 拆分为 M2a（CRC 失败丢块）与 M2b（CRC 失败交下游重同步）
//    - 新增 ParseStatus::Resync 与 ParseResult::resync_from
//    - decode_one() 增加参数 resync_on_badcrc
//
//  五种模式：
//    None            : [payload]                          无边界信息（M0）
//    Prefix          : [2B len][payload]                  裸长度字段（M1）
//    PrefixCrcDrop   : [2B len][2B crc][payload]          CRC 失败丢块（M2a）
//    PrefixCrcResync : [2B len][2B crc][payload]          CRC 失败退重同步（M2b）
//    Chunked         : [2B seq][1022B chunk]              定长分块（M3）
//
//  注意：M2a 与 M2b 的**线上格式完全相同**，差异只在接收端的处理动作。
//
//  编译标准：C++14 及以上
//  设计原则：不依赖 OpenISAC 任何现有代码，可独立编译与单元测试
// =============================================================================

#pragma once

#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>
#include <algorithm>

namespace framing {

// -----------------------------------------------------------------------------
// 一、模式与常量
// -----------------------------------------------------------------------------

enum class Mode : uint8_t {
    None            = 0,   // M0：无边界信息
    Prefix          = 1,   // M1：裸长度字段
    PrefixCrcDrop   = 2,   // M2a：长度 + CRC，失败则丢块
    PrefixCrcResync = 3,   // M2b：长度 + CRC，失败则退重同步
    Chunked         = 4,   // M3：定长分块
};

constexpr size_t kPrefixLen     = 2;   // 长度字段
constexpr size_t kCrcLen        = 2;   // CRC16
constexpr size_t kSeqLen        = 2;   // 序号字段
constexpr size_t kPrefixCrcHead = kPrefixLen + kCrcLen;   // 4
constexpr size_t kChunkedHead   = kSeqLen;                // 2

constexpr size_t kChunkSize    = 1024;                        // 定长块总长
constexpr size_t kChunkPayload = kChunkSize - kChunkedHead;   // 1022

constexpr size_t kMaxPayload = 0xFFFF;

// 失步判定：连续 kMisalignRun 个块无起始码 → 记一次
// ★ 该阈值写入后不得修改（见《实验前判定口径_固定版.md》）
constexpr size_t kMisalignRun = 3;

inline bool is_crc_mode(Mode m) {
    return m == Mode::PrefixCrcDrop || m == Mode::PrefixCrcResync;
}

inline const char* to_string(Mode m) {
    switch (m) {
        case Mode::None:            return "none";
        case Mode::Prefix:          return "prefix";
        case Mode::PrefixCrcDrop:   return "prefix_crc_drop";
        case Mode::PrefixCrcResync: return "prefix_crc_resync";
        case Mode::Chunked:         return "chunked";
    }
    return "unknown";
}

inline bool parse_mode(const std::string& s, Mode& out) {
    if (s == "none")                       { out = Mode::None;             return true; }
    if (s == "prefix")                     { out = Mode::Prefix;           return true; }
    if (s == "prefix_crc" || s == "prefix_crc_drop" || s == "m2a")
                                           { out = Mode::PrefixCrcDrop;    return true; }
    if (s == "prefix_crc_resync" || s == "m2b")
                                           { out = Mode::PrefixCrcResync;  return true; }
    if (s == "chunked" || s == "chunk")    { out = Mode::Chunked;          return true; }
    return false;
}

/// 该模式在线上格式中占的固定头部字节数
inline size_t head_len(Mode m) {
    switch (m) {
        case Mode::None:            return 0;
        case Mode::Prefix:          return kPrefixLen;
        case Mode::PrefixCrcDrop:
        case Mode::PrefixCrcResync: return kPrefixCrcHead;
        case Mode::Chunked:         return kChunkedHead;
    }
    return 0;
}

// -----------------------------------------------------------------------------
// 二、CRC-16/CCITT-FALSE
//     多项式 0x1021、初值 0xFFFF、输入输出均不反转、无末异或
//
//     ★ 只覆盖 2 字节长度字段，不覆盖载荷。
//     理由：若覆盖载荷，M2 会把"载荷错误"也一并处理，与 M1 产生混淆，
//           无法分离"边界保护"与"载荷校验"两个变量。
// -----------------------------------------------------------------------------

inline uint16_t crc16_update(uint16_t crc, const uint8_t* data, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        crc ^= static_cast<uint16_t>(data[i]) << 8;
        for (int b = 0; b < 8; ++b) {
            crc = (crc & 0x8000u)
                ? static_cast<uint16_t>((crc << 1) ^ 0x1021u)
                : static_cast<uint16_t>(crc << 1);
        }
    }
    return crc;
}

inline uint16_t crc16_ccitt(const uint8_t* data, size_t len) {
    return crc16_update(0xFFFFu, data, len);
}

// -----------------------------------------------------------------------------
// 三、发送端
// -----------------------------------------------------------------------------

/// 单包编码（M0 / M1 / M2a / M2b 共用）
///
/// ★ M2a 与 M2b 的线上格式完全相同，编码不做区分。
///
/// @param mode        分帧模式；Chunked 请改用 encode_chunk()
/// @param payload     原始载荷（可 nullptr，当 payload_len==0）
/// @param payload_len 载荷长度
/// @param seq         序号（仅 Chunked 使用，此处仅为接口统一）
/// @param out         输出缓冲区，容量须 >= head_len(mode) + payload_len
/// @param out_cap     输出缓冲区容量
/// @return            写入长度；0 表示失败
inline size_t encode_one(Mode mode,
                         const uint8_t* payload, size_t payload_len,
                         uint16_t /*seq*/,
                         uint8_t* out, size_t out_cap) {
    if (out == nullptr) return 0;
    if (payload_len > 0 && payload == nullptr) return 0;
    if (mode == Mode::Chunked) return 0;

    // 只有带长度字段的模式才受 16 bit 限制
    if (mode != Mode::None && payload_len > kMaxPayload) return 0;

    const size_t h = head_len(mode);
    if (out_cap < h + payload_len) return 0;

    if (mode == Mode::Prefix || is_crc_mode(mode)) {
        out[0] = static_cast<uint8_t>((payload_len >> 8) & 0xFF);
        out[1] = static_cast<uint8_t>(payload_len & 0xFF);
        if (is_crc_mode(mode)) {
            const uint16_t c = crc16_ccitt(out, kPrefixLen);
            out[2] = static_cast<uint8_t>((c >> 8) & 0xFF);
            out[3] = static_cast<uint8_t>(c & 0xFF);
        }
    }

    if (payload_len > 0) std::memcpy(out + h, payload, payload_len);
    return h + payload_len;
}

// ---- Chunked 模式 --------------------------------------------------------

struct ChunkPlan {
    size_t num_chunks;    // 需要的块数
    size_t last_payload;  // 最后一块的实际载荷字节数
    size_t total_bytes;   // num_chunks * kChunkSize
};

inline ChunkPlan plan_chunks(size_t payload_len) {
    ChunkPlan p{0, 0, 0};
    if (payload_len == 0) return p;
    p.num_chunks   = (payload_len + kChunkPayload - 1) / kChunkPayload;
    p.last_payload = payload_len - (p.num_chunks - 1) * kChunkPayload;
    p.total_bytes  = p.num_chunks * kChunkSize;
    return p;
}

/// 编码第 idx 个块（不足部分补 0x00）
inline size_t encode_chunk(size_t idx, uint16_t seq,
                           const uint8_t* payload, size_t payload_len,
                           uint8_t* out, size_t out_cap) {
    if (out == nullptr || out_cap < kChunkSize) return 0;
    const size_t off = idx * kChunkPayload;
    if (off >= payload_len) return 0;

    const size_t avail = std::min(kChunkPayload, payload_len - off);

    out[0] = static_cast<uint8_t>((seq >> 8) & 0xFF);
    out[1] = static_cast<uint8_t>(seq & 0xFF);
    if (avail > 0) std::memcpy(out + kChunkedHead, payload + off, avail);
    if (avail < kChunkPayload) {
        std::memset(out + kChunkedHead + avail, 0x00, kChunkPayload - avail);
    }
    return kChunkSize;
}

// -----------------------------------------------------------------------------
// 四、接收端
// -----------------------------------------------------------------------------

enum class ParseStatus : uint8_t {
    Ok          = 0,   // 成功定界
    NeedMore    = 1,   // 数据不足（流式场景用）
    BadLength   = 2,   // 长度字段非法（越界或为 0）
    BadCrc      = 3,   // CRC 失败 → M2a 丢块
    NoBoundary  = 4,   // 无边界信息（M0）
    Resync      = 5,   // ★ M2b 专用：本块不可信，交下游用起始码重定位
};

inline const char* to_string(ParseStatus s) {
    switch (s) {
        case ParseStatus::Ok:         return "ok";
        case ParseStatus::NeedMore:   return "need_more";
        case ParseStatus::BadLength:  return "bad_length";
        case ParseStatus::BadCrc:     return "bad_crc";
        case ParseStatus::NoBoundary: return "no_boundary";
        case ParseStatus::Resync:     return "resync";
    }
    return "unknown";
}

struct ParseResult {
    ParseStatus    status;
    const uint8_t* payload;     // 有效载荷（指向输入缓冲区内部，不拷贝）
    size_t         len;         // 载荷长度
    size_t         consumed;    // 本次消费字节数
    size_t         resync_from; // ★ M2b：建议下游从该偏移开始寻找起始码
};

/// 解析一段待还原的字节（RS 译码之后、投递给视频解码器之前）
///
/// @param mode              分帧模式（Chunked 请用 decode_chunk）
/// @param buf/len           输入字节
/// @param expect_len        期望的载荷长度（来自帧头 payload_len）
///
/// ★ M2a 与 M2b 的差异由 mode 本身区分，无需额外开关：
///     Mode::PrefixCrcDrop   → CRC 失败返回 BadCrc（调用方丢块）
///     Mode::PrefixCrcResync → CRC 失败返回 Resync，并把整块数据交给下游
///                             （payload 指向 buf，len = 整块长度，
///                               resync_from = 保护头之后的位置）
///
/// ★ M2b 的语义：宁可把"可能错位"的数据交给下游，也不制造字节流空洞。
///   下游（H.264 解码器）能靠起始码自行重定位，比整块丢弃的损伤更小。
inline ParseResult decode_one(Mode mode,
                              const uint8_t* buf, size_t len,
                              size_t expect_len) {
    ParseResult r{ParseStatus::NoBoundary, nullptr, 0, 0, 0};
    if (buf == nullptr) { r.status = ParseStatus::NeedMore; return r; }

    switch (mode) {

    case Mode::None: {
        // 无边界字段，只能用调用方给的长度去猜。
        // ★ 真实系统里 expect_len 的语义是"RS 编码后的长度"，
        //   与原始载荷长度不同，因此 M0 必然切错 —— 这正是 M0 的失败机理。
        if (expect_len == 0 || expect_len > len) {
            r.status = ParseStatus::BadLength;
            return r;
        }
        r.status   = ParseStatus::Ok;
        r.payload  = buf;
        r.len      = expect_len;
        r.consumed = expect_len;
        return r;
    }

    case Mode::Prefix: {
        if (len < kPrefixLen) { r.status = ParseStatus::NeedMore; return r; }
        const size_t L = (static_cast<size_t>(buf[0]) << 8) | buf[1];
        if (L == 0 || L + kPrefixLen > len) {
            r.status = ParseStatus::BadLength;
            return r;
        }
        r.status   = ParseStatus::Ok;
        r.payload  = buf + kPrefixLen;
        r.len      = L;
        r.consumed = kPrefixLen + L;
        return r;
    }

    case Mode::PrefixCrcDrop:
    case Mode::PrefixCrcResync: {
        if (len < kPrefixCrcHead) { r.status = ParseStatus::NeedMore; return r; }

        const uint16_t want = static_cast<uint16_t>(
            (static_cast<uint16_t>(buf[2]) << 8) | buf[3]);
        const uint16_t calc = crc16_ccitt(buf, kPrefixLen);

        // ★ CRC 先于长度检查：长度字段被破坏时，CRC 给出明确的"边界失守"信号，
        //   而不是被误判成 BadLength（那样无法与"载荷不足"区分）。
        if (want != calc) {
            if (mode == Mode::PrefixCrcResync) {
                // M2b：不丢块，把整块交给下游重同步
                r.status      = ParseStatus::Resync;
                r.payload     = buf;                 // 含 4 字节保护头
                r.len         = len;                 // 整块长度
                r.consumed    = len;
                r.resync_from = kPrefixCrcHead;      // 建议从保护头之后开始找
                return r;
            }
            // M2a：丢块
            r.status = ParseStatus::BadCrc;
            return r;
        }

        const size_t L = (static_cast<size_t>(buf[0]) << 8) | buf[1];
        if (L == 0 || L + kPrefixCrcHead > len) {
            r.status = ParseStatus::BadLength;
            return r;
        }
        r.status   = ParseStatus::Ok;
        r.payload  = buf + kPrefixCrcHead;
        r.len      = L;
        r.consumed = kPrefixCrcHead + L;
        return r;
    }

    case Mode::Chunked:
    default:
        return r;   // 请用 decode_chunk
    }
}

// ---- Chunked 解码 --------------------------------------------------------

struct ChunkParseResult {
    ParseStatus    status;
    uint16_t       seq;
    const uint8_t* payload;   // 指向 kChunkPayload 字节
    size_t         len;       // 恒为 kChunkPayload
    bool           seq_gap;   // 与上一块不连续
};

/// 序号连续性判断（正确处理 16 bit 回绕）
/// 错误写法 cur == prev + 1 在 prev==65535 时失效
inline bool is_consecutive(uint16_t prev, uint16_t cur) {
    return static_cast<uint16_t>(cur - prev) == 1;
}

inline ChunkParseResult decode_chunk(const uint8_t* buf, size_t len,
                                     bool has_prev, uint16_t prev_seq) {
    ChunkParseResult r{ParseStatus::NeedMore, 0, nullptr, 0, false};
    if (buf == nullptr || len < kChunkSize) return r;

    r.seq     = static_cast<uint16_t>((static_cast<uint16_t>(buf[0]) << 8) | buf[1]);
    r.payload = buf + kChunkedHead;
    r.len     = kChunkPayload;
    r.status  = ParseStatus::Ok;
    r.seq_gap = has_prev && !is_consecutive(prev_seq, r.seq);
    return r;
}

// -----------------------------------------------------------------------------
// 五、失步检测（misalign_events 的实现基础）
// -----------------------------------------------------------------------------

/// 在 buf[from..len) 中查找 Annex B 起始码 00 00 00 01
/// @return 起始码首字节索引；未找到返回 len
inline size_t find_start_code(const uint8_t* buf, size_t len, size_t from = 0) {
    if (buf == nullptr || len < 4) return len;
    if (from > len - 4) return len;
    for (size_t i = from; i + 3 < len; ++i) {
        if (buf[i] == 0x00 && buf[i + 1] == 0x00 &&
            buf[i + 2] == 0x00 && buf[i + 3] == 0x01) {
            return i;
        }
    }
    return len;
}

inline bool has_start_code(const uint8_t* buf, size_t len) {
    return find_start_code(buf, len, 0) != len;
}

/// 失步累计器：连续 kMisalignRun 块无起始码 → 记一次
class MisalignDetector {
public:
    /// @return true 表示本次触发了新的失步事件（只在达到阈值那一次返回 true）
    bool feed(const uint8_t* buf, size_t len) {
        if (has_start_code(buf, len)) { run_ = 0; return false; }
        ++run_;
        if (run_ == kMisalignRun) return true;
        return false;
    }

    size_t run() const { return run_; }
    void   reset()     { run_ = 0; }

private:
    size_t run_ = 0;
};

} // namespace framing
