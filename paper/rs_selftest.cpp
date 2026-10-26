// rs_selftest.cpp —— 独立自检，不需要任何硬件，不需要 OpenISAC 构建系统
//
// 用法（在有 g++ 的机器上，例如远端 NTN 的 Ubuntu）：
//   cp rs_selftest.cpp <OpenISAC_new>/include/
//   cd <OpenISAC_new>/include
//   g++ -O2 -std=c++17 rs_selftest.cpp -o rs_selftest && ./rs_selftest
//
// 判读：
//   [A] NO  -> 静态表缺陷（_init_tables/_init_gen 的 static bool done）
//   [B] 失败 -> 编码器与伴随式取向不一致（或表缺陷）
//   [C] 前面若干档就失败 -> 解码器 BM/Chien/Forney 有问题
//   全部 OK -> 这份实现是好的，问题不在 RS 本身

#include "ReedSolomon.hpp"
#include <cstdio>
#include <cstring>
#include <vector>

static std::vector<uint8_t> make_msg() {
    std::vector<uint8_t> m(ReedSolomon::K);
    for (int i = 0; i < ReedSolomon::K; ++i) m[i] = static_cast<uint8_t>(i * 37 + 11);
    return m;
}

int main() {
    const auto msg = make_msg();
    int failures = 0;

    // ---------- [A] 静态表缺陷：第 1 个与第 2 个实例的编码结果必须一致 ----------
    ReedSolomon rs_a;                                  // 进程中第 1 个实例
    const auto cw_a = rs_a.encode(msg.data(), msg.size());
    ReedSolomon rs_b;                                  // 第 2 个实例（真实调用路径就是这样）
    const auto cw_b = rs_b.encode(msg.data(), msg.size());

    bool same = (cw_a.size() == cw_b.size()) &&
                std::memcmp(cw_a.data(), cw_b.data(), cw_a.size()) == 0;
    std::printf("[A] 第1/第2实例编码一致 : %s\n", same ? "YES" : "NO   <-- 静态表缺陷");
    if (!same) {
        ++failures;
        int diff = 0;
        for (size_t i = 0; i < cw_a.size() && i < cw_b.size(); ++i)
            if (cw_a[i] != cw_b[i]) ++diff;
        std::printf("    两个码字有 %d/%zu 字节不同；第2实例校验位是否全零: ",
                    diff, cw_b.size());
        bool all_zero = true;
        for (size_t i = ReedSolomon::K; i < cw_b.size(); ++i)
            if (cw_b[i] != 0) { all_zero = false; break; }
        std::printf("%s\n", all_zero ? "是（表全零的确证）" : "否");
    }

    // ---------- [B] 干净码字必须能被解码并原样还原 ----------
    std::vector<uint8_t> out(ReedSolomon::K, 0);
    size_t corrected = 0;
    bool ok = rs_a.decode_with_stats(cw_a.data(), cw_a.size(), out.data(), &corrected);
    bool equal = ok && std::memcmp(out.data(), msg.data(), ReedSolomon::K) == 0;
    std::printf("[B] 干净码字: ok=%d corrected=%zu 还原正确=%d %s\n",
                (int)ok, corrected, (int)equal,
                (equal && corrected == 0) ? "" : "  <-- 编码器/伴随式不自洽");
    if (!(equal && corrected == 0)) ++failures;

    // ---------- [C] 纠错能力扫描：0..16 必须成功且 corrected 精确，17 必须失败 ----------
    std::printf("[C] 纠错扫描（逐档注入字节错误）\n");
    for (int ne = 0; ne <= ReedSolomon::T + 1; ++ne) {
        auto bad = cw_a;
        for (int e = 0; e < ne; ++e) {
            size_t pos = static_cast<size_t>((e * 13) % ReedSolomon::N);
            bad[pos] ^= 0x5A;
        }
        std::memset(out.data(), 0, out.size());
        corrected = 0;
        bool r = rs_a.decode_with_stats(bad.data(), bad.size(), out.data(), &corrected);
        bool good = r && std::memcmp(out.data(), msg.data(), ReedSolomon::K) == 0;
        bool expect = (ne <= ReedSolomon::T);
        bool pass = expect ? (good && corrected == (size_t)ne) : (!good);
        if (!pass) ++failures;
        std::printf("    注入 %2d 个错误 -> 期望%s, 实际 r=%d corrected=%2zu 还原=%d  %s\n",
                    ne, expect ? "成功并还原" : "判为不可纠",
                    (int)r, corrected, (int)good, pass ? "OK" : "<-- FAIL");
    }

    std::printf("\n结论: %s\n", failures == 0
        ? "该 RS 实现通过自检，问题不在编解码器本身。"
        : "该 RS 实现未通过自检，编号见上方 <-- 标记。");
    return failures == 0 ? 0 : 1;
}
