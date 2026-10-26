// =============================================================================
//  test_framing.cpp  —  Framing.hpp v2 的单元自测
//
//  编译（任意平台，不需要 USRP）：
//      g++ -std=c++14 -O2 -Wall -Wextra -Iinclude test_framing.cpp -o test_framing
//      ./test_framing
//
//  覆盖：
//    1. 四种单包模式 round-trip（含边界长度 1/2/255/65535）
//    2. CRC 检出率（16 个长度位全翻转）
//    3. ★ M2a vs M2b 的关键差异（CRC 失败后的行为）
//    4. Chunked 计划与编解码（含 15KB I 帧场景）
//    5. 序号回绕
//    6. 失步检测阈值
//    7. M0 的必然失败
//    8. Stats 冒烟测试
// =============================================================================

#include "Framing.hpp"
#include "FramingStats.hpp"

#include <cstdio>
#include <cstring>
#include <vector>

using namespace framing;

static int g_pass = 0;
static int g_fail = 0;

#define CHECK(cond, msg)                                                  \
    do {                                                                  \
        if (cond) { ++g_pass; }                                           \
        else { ++g_fail; std::printf("  [FAIL] %s (line %d)\n", msg, __LINE__); } \
    } while (0)

// -----------------------------------------------------------------------------
// 工具
// -----------------------------------------------------------------------------

static std::vector<uint8_t> make_payload(size_t n, uint8_t seed = 0x5A) {
    std::vector<uint8_t> v(n);
    for (size_t i = 0; i < n; ++i) {
        v[i] = static_cast<uint8_t>((i * 37 + seed) & 0xFF);
    }
    return v;
}

static void flip_bit(uint8_t* buf, size_t byte_idx, int bit_idx) {
    buf[byte_idx] ^= static_cast<uint8_t>(1u << bit_idx);
}

// 所有"单包"模式（不含 Chunked）
static const Mode kOneShotModes[] = {
    Mode::None, Mode::Prefix, Mode::PrefixCrcDrop, Mode::PrefixCrcResync
};

// -----------------------------------------------------------------------------
// 1. 单包 round-trip
// -----------------------------------------------------------------------------

static void test_roundtrip_one(Mode mode) {
    std::printf("test_roundtrip_one(%s)\n", to_string(mode));

    const size_t lens[] = {1, 2, 7, 63, 255, 1023, 1024, 4096, 65535};
    for (size_t L : lens) {
        auto payload = make_payload(L);
        std::vector<uint8_t> enc(L + 8, 0);

        size_t n = encode_one(mode, payload.data(), L, 0, enc.data(), enc.size());
        CHECK(n == head_len(mode) + L, "encoded length");
        enc.resize(n);

        ParseResult r = decode_one(mode, enc.data(), enc.size(), L);

        if (mode == Mode::None) {
            CHECK(r.status == ParseStatus::Ok, "none with correct expect_len");
            CHECK(r.len == L, "none length");
        } else {
            CHECK(r.status == ParseStatus::Ok, "status ok");
            CHECK(r.len == L, "payload length");
            CHECK(std::memcmp(r.payload, payload.data(), L) == 0, "payload content");
        }
    }
}

// -----------------------------------------------------------------------------
// 2. CRC 检出率
// -----------------------------------------------------------------------------

static void test_crc_detection() {
    std::printf("test_crc_detection\n");

    const size_t L = 512;
    auto payload = make_payload(L);
    std::vector<uint8_t> enc(L + 8, 0);
    size_t n = encode_one(Mode::PrefixCrcDrop, payload.data(), L, 0, enc.data(), enc.size());
    enc.resize(n);

    // 2a. 长度字段 1 bit 错 → 必须被 CRC 检出
    {
        auto bad = enc;
        flip_bit(bad.data(), 0, 3);
        ParseResult r = decode_one(Mode::PrefixCrcDrop, bad.data(), bad.size(), L);
        CHECK(r.status == ParseStatus::BadCrc, "1-bit in len -> BadCrc");
    }

    // 2b. CRC 字段自身 1 bit 错 → 必须被检出
    {
        auto bad = enc;
        flip_bit(bad.data(), 2, 0);
        ParseResult r = decode_one(Mode::PrefixCrcDrop, bad.data(), bad.size(), L);
        CHECK(r.status == ParseStatus::BadCrc, "1-bit in crc -> BadCrc");
    }

    // 2c. 载荷 1 bit 错 → 不应触发 BadCrc（本设计只保护边界）
    {
        auto bad = enc;
        flip_bit(bad.data(), kPrefixCrcHead + 10, 5);
        ParseResult r = decode_one(Mode::PrefixCrcDrop, bad.data(), bad.size(), L);
        CHECK(r.status == ParseStatus::Ok, "payload bit-flip should NOT be BadCrc");
    }

    // 2d. 遍历 16 个长度位，全部应被检出
    {
        int detected = 0, total = 0;
        for (int byte = 0; byte < 2; ++byte) {
            for (int bit = 0; bit < 8; ++bit) {
                auto bad = enc;
                flip_bit(bad.data(), byte, bit);
                ParseResult r = decode_one(Mode::PrefixCrcDrop, bad.data(), bad.size(), L);
                ++total;
                if (r.status == ParseStatus::BadCrc) ++detected;
            }
        }
        CHECK(detected == total, "all 16 len-bit flips detected");
        std::printf("  len-bit flips: %d/%d detected\n", detected, total);
    }

    // 2e. M2b 同样的注入，必须返回 Resync 而不是 BadCrc
    {
        auto bad = enc;
        flip_bit(bad.data(), 0, 3);
        ParseResult r = decode_one(Mode::PrefixCrcResync, bad.data(), bad.size(), L);
        CHECK(r.status == ParseStatus::Resync, "M2b: BadCrc -> Resync");
    }
}

// -----------------------------------------------------------------------------
// ★ 3. M2a vs M2b 的关键差异
// -----------------------------------------------------------------------------

static void test_m2a_vs_m2b() {
    std::printf("test_m2a_vs_m2b\n");

    const size_t L = 800;
    auto payload = make_payload(L);
    // 在载荷里埋一个起始码，模拟 H.264 NAL 边界
    payload[100] = 0x00; payload[101] = 0x00;
    payload[102] = 0x00; payload[103] = 0x01;

    std::vector<uint8_t> enc(L + 8, 0);
    size_t n = encode_one(Mode::PrefixCrcDrop, payload.data(), L, 0, enc.data(), enc.size());
    enc.resize(n);

    // 破坏长度字段
    auto bad = enc;
    flip_bit(bad.data(), 0, 7);

    // --- M2a：丢块 ---
    ParseResult ra = decode_one(Mode::PrefixCrcDrop, bad.data(), bad.size(), L);
    CHECK(ra.status == ParseStatus::BadCrc, "M2a status");
    CHECK(ra.payload == nullptr, "M2a delivers nothing");

    // --- M2b：交下游重同步 ---
    ParseResult rb = decode_one(Mode::PrefixCrcResync, bad.data(), bad.size(), L);
    CHECK(rb.status == ParseStatus::Resync, "M2b status");
    CHECK(rb.payload == bad.data(), "M2b delivers whole block");
    CHECK(rb.len == bad.size(), "M2b len == block size");
    CHECK(rb.resync_from == kPrefixCrcHead, "M2b resync_from == head len");

    // ★ 关键：M2b 交付的数据里，起始码仍可被找到
    //   这正是"不制造空洞"的价值：下游能自行定位
    const uint8_t* body = rb.payload + rb.resync_from;
    size_t body_len = rb.len - rb.resync_from;
    CHECK(has_start_code(body, body_len), "M2b: start code still findable in delivered block");

    std::printf("  M2a: drop(%zu bytes lost) | M2b: deliver %zu bytes, start code %s\n",
                bad.size(), rb.len,
                has_start_code(body, body_len) ? "FOUND" : "MISSING");
}

// -----------------------------------------------------------------------------
// 4. Chunked
// -----------------------------------------------------------------------------

static void test_chunked() {
    std::printf("test_chunked\n");

    // 4a. 计划
    {
        auto p1 = plan_chunks(0);
        CHECK(p1.num_chunks == 0, "plan(0)");

        auto p2 = plan_chunks(1);
        CHECK(p2.num_chunks == 1 && p2.last_payload == 1, "plan(1)");

        auto p3 = plan_chunks(kChunkPayload);
        CHECK(p3.num_chunks == 1 && p3.last_payload == kChunkPayload, "plan(exact)");

        auto p4 = plan_chunks(kChunkPayload + 1);
        CHECK(p4.num_chunks == 2 && p4.last_payload == 1, "plan(+1)");

        auto p5 = plan_chunks(15000);
        CHECK(p5.num_chunks == 15, "plan(15KB) == 15 chunks");
        std::printf("  15KB -> %zu chunks, last=%zu, total=%zu\n",
                    p5.num_chunks, p5.last_payload, p5.total_bytes);
    }

    // 4b. round-trip
    {
        const size_t L = kChunkPayload * 3 + 500;
        auto payload = make_payload(L);
        auto plan = plan_chunks(L);

        std::vector<uint8_t> rebuilt;
        rebuilt.reserve(plan.total_bytes);
        uint16_t prev = 0;
        bool has_prev = false;
        int gaps = 0;

        for (size_t i = 0; i < plan.num_chunks; ++i) {
            uint8_t chunk[kChunkSize];
            size_t nn = encode_chunk(i, static_cast<uint16_t>(100 + i),
                                     payload.data(), L, chunk, sizeof(chunk));
            CHECK(nn == kChunkSize, "chunk size");

            auto r = decode_chunk(chunk, nn, has_prev, prev);
            CHECK(r.status == ParseStatus::Ok, "chunk decode ok");
            if (r.seq_gap) ++gaps;
            prev = r.seq;
            has_prev = true;
            rebuilt.insert(rebuilt.end(), r.payload, r.payload + r.len);
        }

        CHECK(gaps == 0, "no seq gap");
        CHECK(rebuilt.size() >= L, "rebuilt long enough");
        CHECK(std::memcmp(rebuilt.data(), payload.data(), L) == 0, "rebuilt content");
    }

    // 4c. 序号回绕
    {
        CHECK(is_consecutive(0, 1), "0->1");
        CHECK(is_consecutive(65534, 65535), "65534->65535");
        CHECK(is_consecutive(65535, 0), "65535->0 wrap");
        CHECK(!is_consecutive(65535, 2), "65535->2 not consecutive");
        CHECK(!is_consecutive(5, 5), "same seq not consecutive");
    }

    // 4d. 丢中间一块，后续块边界仍正确
    {
        const size_t L = kChunkPayload * 4;
        auto payload = make_payload(L);
        auto plan = plan_chunks(L);

        bool saw_gap = false;
        uint16_t prev = 0;
        bool has_prev = false;

        for (size_t i = 0; i < plan.num_chunks; ++i) {
            if (i == 2) continue;   // 模拟第 2 块丢失（LDPC 失败）
            uint8_t chunk[kChunkSize];
            encode_chunk(i, static_cast<uint16_t>(i), payload.data(), L, chunk, sizeof(chunk));
            if (i == 2) { has_prev = false; continue; }
            auto r = decode_chunk(chunk, kChunkSize, has_prev, prev);
            if (r.seq_gap) saw_gap = true;
            prev = r.seq;
            has_prev = true;
        }
        CHECK(saw_gap, "missing chunk detected as seq_gap");
    }
}

// -----------------------------------------------------------------------------
// 5. 起始码与失步
// -----------------------------------------------------------------------------

static void test_start_code() {
    std::printf("test_start_code\n");

    const uint8_t s[] = {0x00, 0x00, 0x00, 0x01, 0x67, 0x42};
    CHECK(find_start_code(s, sizeof(s), 0) == 0, "start code at 0");
    CHECK(has_start_code(s, sizeof(s)), "has start code");

    const uint8_t no_s[] = {0x11, 0x22, 0x00, 0x00, 0x33, 0x01};
    CHECK(!has_start_code(no_s, sizeof(no_s)), "no start code");

    const uint8_t s2[] = {0xAA, 0xBB, 0x00, 0x00, 0x00, 0x01};
    CHECK(find_start_code(s2, sizeof(s2), 0) == 2, "start code at 2");

    const uint8_t tiny[] = {0x00, 0x00, 0x00};
    CHECK(find_start_code(tiny, 3, 0) == 3, "too short returns len");
}

static void test_misalign_detector() {
    std::printf("test_misalign_detector\n");

    const uint8_t good[] = {0x00, 0x00, 0x00, 0x01, 0x67};
    const uint8_t bad[]  = {0x11, 0x22, 0x33, 0x44, 0x55};

    MisalignDetector d;

    CHECK(!d.feed(good, sizeof(good)), "good block no event");
    CHECK(d.run() == 0, "run reset after good");

    CHECK(!d.feed(bad, sizeof(bad)), "bad #1 no event");
    CHECK(!d.feed(bad, sizeof(bad)), "bad #2 no event");
    CHECK(d.feed(bad, sizeof(bad)), "bad #3 triggers");
    CHECK(!d.feed(bad, sizeof(bad)), "bad #4 no repeat");

    CHECK(!d.feed(good, sizeof(good)), "good resets");
    CHECK(d.run() == 0, "run reset");
}

// -----------------------------------------------------------------------------
// 6. M0 的必然失败
// -----------------------------------------------------------------------------

static void test_none_mode_fails() {
    std::printf("test_none_mode_fails\n");

    const size_t payload_len = 1000;
    const size_t rs_len      = 1275;      // 5 个 RS 码字
    const size_t buf_len     = 1323;      // 补齐到 21 个 LDPC 块

    std::vector<uint8_t> buf(buf_len, 0);
    for (size_t i = 0; i < payload_len; ++i) buf[i] = static_cast<uint8_t>(i & 0xFF);

    // M0：用错误的长度（rs_len）去切
    ParseResult r = decode_one(Mode::None, buf.data(), buf.size(), rs_len);
    CHECK(r.status == ParseStatus::Ok, "none accepts rs_len blindly");
    CHECK(r.len == rs_len, "none takes 1275 bytes");
    CHECK(r.len > payload_len, "took MORE than actual payload -> garbage tail");

    std::printf("  M0 切出 %zu 字节，真实载荷 %zu 字节，多出 %ld 字节垃圾\n",
                r.len, payload_len, static_cast<long>(r.len) - static_cast<long>(payload_len));

    // 期望长度超过缓冲区 → BadLength
    ParseResult r2 = decode_one(Mode::None, buf.data(), buf.size(), buf_len + 100);
    CHECK(r2.status == ParseStatus::BadLength, "none fails when expect_len > buf");
}

// -----------------------------------------------------------------------------
// 7. Stats
// -----------------------------------------------------------------------------

static void test_stats() {
    std::printf("test_stats\n");

    Stats s;
    for (int i = 0; i < 200; ++i) { s.on_block(); s.maybe_report(); }
    s.on_drop();
    s.on_resync();
    s.on_seq_gap();
    s.on_misalign();
    s.on_deliver(1000);
    s.on_recover(8);

    CHECK(s.blocks_total() == 200, "blocks");
    CHECK(s.framing_drop() == 1, "drop");
    CHECK(s.resync_count() == 1, "resync");
    CHECK(s.misalign_events() == 1, "misalign");
    CHECK(s.bytes_delivered() == 1000, "delivered");
    s.report();
}

// -----------------------------------------------------------------------------

int main() {
    std::printf("========== Framing self-test (v2, 5 modes) ==========\n\n");

    for (Mode m : kOneShotModes) test_roundtrip_one(m);
    test_crc_detection();
    test_m2a_vs_m2b();
    test_chunked();
    test_start_code();
    test_misalign_detector();
    test_none_mode_fails();
    test_stats();

    std::printf("\n========== %d passed, %d failed ==========\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
