# Framing.hpp 接口设计

> **设计日期**：2026-10-23
> **用途**：四模式分帧的纯函数接口。**独立新文件，不依赖任何现有代码。**
> **落地方式**：直接新增到 `include/Framing.hpp`，`#include` 即可用，不需要改动现有文件。
> **约定**：所有函数不抛异常、不做内存分配以外的副作用、不打印日志（统计由 `FramingStats.hpp` 负责）。

---

## 一、设计目标与边界

### 要解决什么

在"变长 UDP 载荷 → RS 码字 → LDPC 定长块"的链路上，提供四种边界约定方式，使同一套收发代码可以通过配置切换：

| 模式 | 边界依据 | 对应论文实验组 |
|---|---|---|
| `Prefix` | 2 字节长度字段 | M1 |
| `PrefixCrc` | 2 字节长度 + 2 字节 CRC16 | M2 |
| `Chunked` | 固定块长（靠配置） | M3 |
| `None` | 无（对照组） | M0 |

### 不解决什么

- **不做纠错**（那是 RS 层的事）
- **不做流控**（溢出由调用方处理）
- **不判断视频内容**（不解析 NAL，只看起始码用于失步检测）
- **不负责统计**（交给 `FramingStats`）

---

## 二、枚举与常量

```cpp
// include/Framing.hpp
#pragma once

#include <cstdint>
#include <cstddef>
#include <vector>
#include <string>

namespace framing {

enum class Mode : uint8_t {
    None       = 0,   // M0：直接透传，不加任何边界信息
    Prefix     = 1,   // M1：[2B len][payload]
    PrefixCrc  = 2,   // M2：[2B len][2B crc16(len)][payload]
    Chunked    = 3,   // M3：[2B seq][chunk]，固定块长
};

// ---- 线上格式的固定开销（字节）----
constexpr size_t kPrefixLen      = 2;   // 长度字段
constexpr size_t kCrcLen         = 2;   // CRC16
constexpr size_t kSeqLen         = 2;   // 序号字段
constexpr size_t kPrefixCrcHead  = kPrefixLen + kCrcLen;  // = 4
constexpr size_t kChunkedHead    = kSeqLen;               // = 2

// ---- Chunked 模式的块尺寸 ----
// 1024 = 2(seq) + 1022(payload)
// 说明：1022 是"每块载荷"的名义长度；实际装多少由调用方给的 available 决定，
//       不足 1022 时末尾补 0x00（补多少由返回的 padded 字段告知）。
constexpr size_t kChunkSize      = 1024;
constexpr size_t kChunkPayload   = kChunkSize - kChunkedHead;  // = 1022

// ---- Annex B 起始码 ----
constexpr uint8_t kStartCode[4] = {0x00, 0x00, 0x00, 0x01};

// ---- 模式名（用于日志与配置解析）----
const char* to_string(Mode m);          // "none" / "prefix" / "prefix_crc" / "chunked"
bool        parse_mode(const std::string& s, Mode& out);  // 失败返回 false

} // namespace framing
```

**为什么把常量放这里**：四个模式的开销在论文里要算得很清楚（`2B` / `4B` / `2B`），放同一处便于核对。

---

## 三、CRC16（CCITT-FALSE）

```cpp
namespace framing {

/// CRC-16/CCITT-FALSE：poly=0x1021, init=0xFFFF, 无反转, 无末异或
/// 选用理由：实现简单、无需查表也能跑；对 2 字节输入足够。
uint16_t crc16_ccitt(const uint8_t* data, size_t len);

/// 递增式版本（若需要覆盖 len 之后的若干字节）
uint16_t crc16_update(uint16_t crc, const uint8_t* data, size_t len);

} // namespace framing
```

**关键设计决定**：**CRC 只覆盖 2 字节长度字段，不覆盖载荷。**

| 方案 | 开销 | 能检出什么 | 是否采纳 |
|---|---|---|---|
| 只覆盖 len | 2B | 长度字段被破坏 | ✅ **采纳** |
| 覆盖 len + 载荷 | 2B | 同上 + 载荷损伤 | ❌ 不采纳 |

**理由**：本实验要验证的是"**边界字段**是否被保护"，不是"载荷是否完整"。若 CRC 覆盖载荷，则 M2 组会把"载荷错误"也一并丢掉，**混淆了自变量**——你无法区分改善来自"边界被保护"还是"载荷被校验"。

> 这一条如果被审稿人问，就是标准的混淆变量排除。

---

## 四、发送端编码

### 4.1 单包编码（M0 / M1 / M2）

```cpp
namespace framing {

struct EncodeResult {
    const uint8_t* data;    // 指向输出缓冲区
    size_t         len;     // 输出长度
};

/// 把一段变长载荷封装为待送入 RS 的字节流。
///
/// 参数：
///   mode      —— 分帧模式（None / Prefix / PrefixCrc 有效；Chunked 见 4.2）
///   payload   —— 原始载荷
///   payload_len —— 载荷长度（<= 65535）
///   seq       —— 序号（Prefix/PrefixCrc 不使用；保留给统计对齐）
///   out       —— 输出缓冲区（调用方提供，容量须 >= payload_len + 4）
///
/// 返回：实际写入长度；0 表示失败（参数非法或缓冲区不足）
///
size_t encode_one(Mode mode,
                  const uint8_t* payload, size_t payload_len,
                  uint16_t seq,
                  uint8_t* out, size_t out_cap);

} // namespace framing
```

**三种模式的输出格式**

```
None       : [payload]                                len = payload_len
Prefix     : [len_hi][len_lo][payload]                len = 2 + payload_len
PrefixCrc  : [len_hi][len_lo][crc_hi][crc_lo][payload] len = 4 + payload_len
```

**参数校验（失败返回 0）**

| 检查 | 原因 |
|---|---|
| `payload == nullptr && payload_len > 0` | 空指针 |
| `payload_len > 0xFFFF` | 长度字段只有 2 字节 |
| `out_cap < payload_len + head` | 缓冲区不足 |

**注意**：`None` 模式下 `payload_len > 0xFFFF` 是**允许**的（没有长度字段限制），但此时接收端必然无法定界——这正是 M0 组要展示的。

---

### 4.2 分块编码（M3 / Chunked）

```cpp
namespace framing {

struct ChunkPlan {
    size_t   num_chunks;     // 需要几个 1024 B 块
    size_t   last_payload;   // 最后一块实际载荷字节数（其余补 0）
    size_t   total_bytes;    // num_chunks * 1024
};

/// 计算把 payload_len 拆成固定块需要的块数
ChunkPlan plan_chunks(size_t payload_len);

/// 编码第 idx 个块
///   out 必须至少 kChunkSize 字节
///   不足部分补 0x00
/// 返回：实际写入长度（恒为 kChunkSize）；0 表示失败
size_t encode_chunk(size_t idx, uint16_t seq,
                    const uint8_t* payload, size_t payload_len,
                    uint8_t* out, size_t out_cap);

} // namespace framing
```

**Chunked 的关键边界问题（今天必须想清楚）**

| 问题 | 决定 | 理由 |
|---|---|---|
| **1 个 I 帧 15 KB 怎么办** | 拆成 ⌈15000/1022⌉ = **15 块** | 块数由 `plan_chunks()` 给出 |
| **seq 是"包序号"还是"块序号"** | **块序号**（每块 +1） | 若用包序号，跨包的块无法用 seq 检测缺口 |
| **seq 16 bit 回绕** | 允许回绕，检测时用 `(uint16_t)(cur - last) == 1` 判断连续 | 65536 块 ≈ 65 秒一轮；用差值比较天然处理回绕 |
| **最后一块补 0x00，接收端怎么知道真实长度** | **靠 H.264 自身定界**（Annex B 起始码） | 这是 M3 的代价：**丧失报文边界**，换取"永不失步" |
| **丢了中间一块怎么办** | 后续块仍然对齐（因为块长固定），只是字节流有洞 | 解码器按起始码重同步，局部损伤 |

> **"最后一块补 0x00 会不会让解码器读到假边界"**：不会。0x00 不是 NAL 起始码的一部分（起始码是 `00 00 00 01`），连续 0x00 只会被当作填充或非法 NAL 而跳过。
> **但这一点需要实测确认**——正是 A1/A2 要验的（GStreamer 能否接受任意 1024 B 的 buffer）。

---

## 五、接收端解码

### 5.1 单包解码（M0 / M1 / M2）

```cpp
namespace framing {

enum class ParseStatus : uint8_t {
    Ok          = 0,   // 成功解析出载荷
    NeedMore    = 1,   // 数据不足（流式场景用），本次无法判定
    BadLength   = 2,   // 长度字段非法（超出缓冲区 / 为 0）
    BadCrc      = 3,   // CRC 校验失败
    NoBoundary  = 4,   // None 模式下无法定界
};

struct ParseResult {
    ParseStatus status;
    const uint8_t* payload;   // 有效载荷起始（指向输入缓冲区内部，不拷贝）
    size_t         len;       // 载荷长度
    size_t         consumed;  // 本次消费了多少字节（用于流式推进）
};

/// 解析一段待还原的字节（RS 译码之后、投递给视频解码器之前）
///
/// 参数：
///   mode  —— 分帧模式
///   buf/len —— 输入字节
///   expect_len —— 调用方"期望"的载荷长度（来自帧头 payload_len）；
///                 None 模式下唯一可用的定界线索；其余模式仅用于交叉校验
///
ParseResult decode_one(Mode mode,
                       const uint8_t* buf, size_t len,
                       size_t expect_len);

} // namespace framing
```

**各模式的行为**

| 模式 | 行为 | 失败时 |
|---|---|---|
| `None` | **无法定界**。若 `expect_len` 合理则按它截取，否则返回 `NoBoundary` | `NoBoundary` |
| `Prefix` | 读 2 字节 len，校验 `2+len <= buf_len` 后截取 | `BadLength` |
| `PrefixCrc` | 读 len + crc，先验 CRC 再截取 | **`BadCrc` → 调用方应丢该块，不切分** |

**M0 的语义要特别注意**

`None` 模式下 `expect_len` 从哪来？**只能来自帧头的 `payload_len`**（那是 RS 编码后的长度，不是原始载荷长度）。

所以 `None` 模式实际上是**用错误的长度去切**——这正是它必然失败的原因。**这一点要在论文里写清楚**：M0 不是"没有长度信息"，而是"用了一个语义不对的长度信息"。

> 如果想让 M0 更"干净"，可以加一个变体 `NoneRaw`：完全按 `expect_len` 截取，不做任何检查。
> **建议保留两种**：`None`（用错长度）与 `NoneRaw`（盲目截取），看哪组冻结率更高。

---

### 5.2 分块解码（M3 / Chunked）

```cpp
namespace framing {

struct ChunkParseResult {
    ParseStatus status;
    uint16_t    seq;          // 该块的序号
    const uint8_t* payload;   // 1022 字节（可能含尾部补零）
    size_t       len;         // 恒为 kChunkPayload（补零也保留，交给下游）
    bool         seq_gap;     // 与上一块不连续
};

/// 解析一个固定块
ChunkParseResult decode_chunk(const uint8_t* buf, size_t len, uint16_t last_seq);

} // namespace framing
```

**seq 连续性判断（含回绕）**

```cpp
// 正确写法：用差值，而不是直接比较
bool is_consecutive(uint16_t prev, uint16_t cur) {
    return static_cast<uint16_t>(cur - prev) == 1;
}
```

> 这行代码值得单独说明：直接写 `cur == prev + 1` 在 `prev == 65535` 时会失败。
> **论文里不必提，但代码里必须对。**

---

## 六、失步检测（`misalign_events` 的实现基础）

```cpp
namespace framing {

/// 在字节流中查找 Annex B 起始码
/// 返回：起始码位置索引；找不到返回 len
size_t find_start_code(const uint8_t* buf, size_t len, size_t from = 0);

/// 判定这一段是否"可解析"：至少含一个起始码
bool has_start_code(const uint8_t* buf, size_t len);

} // namespace framing
```

**`misalign_events` 的判定规则（必须固定）**

> 连续 **3 个块**内均未找到起始码 → 记 1 次失步事件。

**为什么是 3 块而不是 1 块**：

- 单个块可能恰好跨在 NAL 中间（没有完整起始码），这不算失步
- 连续 3 块都没有起始码，说明字节流严重错位
- **这个阈值必须在跑实验前定死并写进论文**，否则会被质疑"调参调到想要的结果"

**可选增强**：同时记录"连续无起始码的块数分布"，画图时能显示失步的严重程度，而不只是一个计数。

---

## 七、统计接口（`FramingStats.hpp`）

```cpp
// include/FramingStats.hpp
#pragma once
#include <cstdint>
#include <cstdio>

namespace framing {

class Stats {
public:
    void on_block()                 { ++blocks_total_; }
    void on_drop()                  { ++framing_drop_; }
    void on_seq_gap()               { ++seq_gap_; }
    void on_misalign()              { ++misalign_events_; }
    void on_deliver(size_t n)       { bytes_delivered_ += n; }
    void on_recover(size_t blocks)  { recover_blocks_sum_ += blocks; ++recover_count_; }

    /// 每 200 块打印一次（与上游 [RS] ok=... 的节奏一致）
    void maybe_report(uint64_t now_blocks);

    /// 强制输出一次（实验结束时调用）
    void report() const;

    void reset();

private:
    uint64_t blocks_total_       = 0;
    uint64_t framing_drop_       = 0;
    uint64_t seq_gap_            = 0;
    uint64_t misalign_events_    = 0;
    uint64_t bytes_delivered_    = 0;
    uint64_t recover_blocks_sum_ = 0;
    uint64_t recover_count_      = 0;
    uint64_t last_report_blocks_ = 0;
};

} // namespace framing
```

**输出格式建议（便于脚本解析）**

```
[FRAMING] blocks=12000 drop=3 gap=1 misalign=2 delivered=11776000 recover_avg=8.5
```

**单行、固定字段顺序、无中文**——这样 Excel 和 Python 都能直接解析。

---

## 八、接入点说明（不写补丁，只标位置）

### 发送端

**位置**：`OFDMModulator.cpp` 中 `_encode_and_enqueue_payload()` 内，**RS 编码之前**。

**当前逻辑**（上游原版）：

```cpp
rs_input.push_back(len_hi);
rs_input.push_back(len_lo);
rs_input.insert(rs_input.end(), payload_data, payload_data + payload_len);
rs_encoded = _rs.encode(rs_input.data(), rs_input.size());
```

**改造后**：

```cpp
// 【新增】按模式构造待编码字节
std::vector<uint8_t> framed;
framed.resize(payload_len + 4);   // 最多 4 字节头
size_t framed_len = framing::encode_one(_framing_mode,
                                        payload_data, payload_len,
                                        _seq++,
                                        framed.data(), framed.size());
if (framed_len == 0) { /* 记录错误，丢弃本包 */ }
rs_encoded = _rs.encode(framed.data(), framed_len);
```

**变量名待确认**：`_framing_mode`、`_seq` 需新增为成员。其余变量名以设备端为准。

---

### 接收端

**位置**：`OFDMDemodulator.cpp` 中，**RS 译码之后、投递给视频解码器之前**。

**当前逻辑**（上游原版）：

```cpp
uint16_t orig_len = (rs_decoded[0] << 8) | rs_decoded[1];
udp_data.assign(rs_decoded.begin() + 2, rs_decoded.begin() + 2 + orig_len);
```

**改造后**：

```cpp
auto r = framing::decode_one(_framing_mode,
                             rs_decoded.data(), rs_decoded.size(),
                             payload_len);   // 帧头给的期望长度
if (r.status == framing::ParseStatus::Ok) {
    stats_.on_deliver(r.len);
    udp_data.assign(r.payload, r.payload + r.len);
} else {
    stats_.on_drop();           // BadCrc / BadLength / NoBoundary
    // M2 语义：丢该块，不盲目切分
    return;
}
```

**关键**：`BadCrc` 时**必须直接丢弃**，不能"尽力尝试切分"。这是 M2 与 M1 的唯一区别，也是实验的自变量。

---

## 九、今天必须想清楚的六个边界问题

| # | 问题 | 建议决定 | 若不决定会怎样 |
|---|---|---|---|
| 1 | CRC 覆盖 2 字节还是含载荷 | **只覆盖 2 字节** | 混淆自变量 |
| 2 | Chunked 用块序号还是包序号 | **块序号** | 跨包块无法检测缺口 |
| 3 | 最后一块补零，接收端怎么知道真实长度 | **靠 Annex B 定界** | M3 的代价，必须接受 |
| 4 | 失步判定阈值 | **连续 3 块无起始码** | 会被质疑调参 |
| 5 | `None` 模式的 `expect_len` 从哪来 | **帧头 payload_len（语义错）** | M0 定义不清 |
| 6 | `payload_len > 65535` 怎么办 | `None` 允许，其余拒绝 | 大 I 帧被静默丢弃 |

**第 6 条是实测会撞上的**：你现在的 RS 编码是按 1024 字节包走的，所以 payload 不会超 65535。但**如果以后要传大帧，M1/M2 会直接失败**。建议在 `encode_one()` 里明确返回 0，调用方打日志——**不要静默截断**。

---

## 十、与其他文件的关系

```
include/Framing.hpp         ← 今天写这个（纯函数，零依赖）
include/FramingStats.hpp    ← 今天写这个（计数器）
OFDMModulator.cpp           ← 明天在设备上改（一行调用）
OFDMDemodulator.cpp         ← 明天在设备上改（一行调用）
```

**`Framing.hpp` 可以完全独立编译与单测**：

```cpp
// 一个 30 行的自测程序就能验证全部逻辑，不需要 USRP
int main() {
    uint8_t buf[2048];
    uint8_t payload[1000] = {0};
    // 三种模式各跑一遍 encode → decode，检查 round-trip
    // 注入 1/2/3 bit 错误，检查 CRC 检出率
}
```

**这一点很重要**：今天写的代码，**明天上设备前就能验证正确**，不占用宝贵的设备时间。

---

## 附：今天的最小交付物

| 文件 | 内容 | 工时 |
|---|---|---|
| `include/Framing.hpp` | 枚举 + 常量 + CRC16 + encode_one + decode_one + chunk 相关 + 起始码查找 | 3h |
| `include/FramingStats.hpp` | 计数器 + 定期打印 | 1h |
| `test_framing.cpp` | round-trip + 错误注入自测 | 1h |
| `sim_framing.py` | 三模式失步率 vs p 曲线 | 2h |
| 本文档 | 接口说明（给明天的自己看） | — |

**合计约 7 小时，零风险，全部可独立验证。**
