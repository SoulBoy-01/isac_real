// ============================================================================
//  rs_selftest_single.cpp
//  自包含 RS 自检：内含 ReedSolomon.hpp 原文 + 测试主程序，单文件即可编译运行
//  用法:  g++ -O2 -std=c++17 rs_selftest_single.cpp -o t && ./t
//  或直接粘贴到 https://www.onlinegdb.com / https://godbolt.org 运行
// ============================================================================
#ifndef REED_SOLOMON_HPP
#define REED_SOLOMON_HPP

#include <array>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <vector>

/**
 * @brief Reed-Solomon RS(255, 223) codec over GF(2^8).
 *
 * Corrects up to 16 byte errors per 255-byte codeword.
 * Primitive polynomial: x^8 + x^4 + x^3 + x^2 + 1 (0x11D).
 *
 * Usage:
 *   ReedSolomon rs;
 *   std::vector<uint8_t> encoded = rs.encode(data, data_len);
 *   std::vector<uint8_t> decoded = rs.decode(encoded);
 */
class ReedSolomon {
public:
    static constexpr int N = 255;   // codeword length (bytes)
    static constexpr int K = 223;   // message length (bytes)
    static constexpr int T = 16;    // error correction capability (bytes)
    static constexpr int NPAR = N - K;  // 32 parity bytes

    ReedSolomon() { _init_tables(); }

    /** RS-encode a byte buffer. Returns N bytes per K-byte input block,
     *  with parity appended (systematic encoding). Handles partial final
     *  block by padding with zeros. */
    std::vector<uint8_t> encode(const uint8_t* data, size_t len) const {
        const size_t full_blocks = len / K;
        const size_t rem = len % K;
        const size_t total_blocks = full_blocks + (rem > 0 ? 1 : 0);
        std::vector<uint8_t> out(total_blocks * N);
        for (size_t b = 0; b < full_blocks; ++b) {
            _encode_block(data + b * K, out.data() + b * N);
        }
        if (rem > 0) {
            std::array<uint8_t, K> padded{};
            std::memcpy(padded.data(), data + full_blocks * K, rem);
            _encode_block(padded.data(), out.data() + full_blocks * N);
        }
        return out;
    }

    /** RS-decode a buffer produced by encode(). Returns K*blocks bytes.
     *  Returns empty vector on uncorrectable error. */
    std::vector<uint8_t> decode(const uint8_t* data, size_t len) const {
        if (len == 0 || (len % N) != 0) return {};
        const size_t blocks = len / N;
        std::vector<uint8_t> out(blocks * K);
        for (size_t b = 0; b < blocks; ++b) {
            if (!_decode_block(data + b * N, out.data() + b * K)) {
                return {};  // uncorrectable
            }
        }
        return out;
    }

    /** Decode with info about how many errors were corrected. */
    bool decode_with_stats(const uint8_t* data, size_t len,
                           uint8_t* out, size_t* errors_corrected) const {
        if (len == 0 || (len % N) != 0) return false;
        const size_t blocks = len / N;
        size_t total_errors = 0;
        for (size_t b = 0; b < blocks; ++b) {
            if (!_decode_block(data + b * N, out + b * K)) return false;
            total_errors += _last_corrected;
        }
        if (errors_corrected) *errors_corrected = total_errors;
        return true;
    }

private:
    // ── GF(2^8) tables ──
    static constexpr uint16_t GF_SIZE = 256;
    static constexpr uint16_t GF_PRIMITIVE = 0x11D;

    alignas(64) uint8_t  _exp[GF_SIZE * 2]{};   // α^i
    alignas(64) uint8_t  _log[GF_SIZE]{};       // log_α(x)
    mutable int _last_corrected = 0;

    void _init_tables() {
        static bool done = false;
        if (done) return;
        done = true;
        uint16_t x = 1;
        for (int i = 0; i < 255; ++i) {
            _exp[i] = static_cast<uint8_t>(x);
            _exp[i + 255] = static_cast<uint8_t>(x);
            _log[x] = static_cast<uint8_t>(i);
            x <<= 1;
            if (x & 0x100) x ^= GF_PRIMITIVE;
        }
        _log[0] = 0;  // undefined, treat as 0
    }

    uint8_t _gf_add(uint8_t a, uint8_t b) const { return a ^ b; }
    uint8_t _gf_mul(uint8_t a, uint8_t b) const {
        if (a == 0 || b == 0) return 0;
        return _exp[_log[a] + _log[b]];
    }
    uint8_t _gf_inv(uint8_t a) const {
        if (a == 0) return 0;
        return _exp[255 - _log[a]];
    }
    uint8_t _gf_pow(uint8_t a, int n) const {
        if (a == 0) return 0;
        if (n == 0) return 1;
        return _exp[(_log[a] * n) % 255];
    }

    // ── Generator polynomial coefficients (x^32 + ...) ──
    // g(x) = (x-α^0)(x-α^1)...(x-α^31), stored as g[0] + g[1]x + ... + g[32]x^32
    static constexpr int GEN_DEG = NPAR;  // 32
    alignas(32) uint8_t _gen[GEN_DEG + 1]{};

    void _init_gen() {
        static bool done = false;
        if (done) return;
        done = true;
        _gen[0] = 1;
        for (int i = 0; i < GEN_DEG; ++i) {
            // multiply by (x - α^i) = (x + α^i) since in GF(2), + = -
            uint8_t alpha_i = _exp[i];
            for (int j = GEN_DEG; j > 0; --j) {
                _gen[j] = _gf_add(_gen[j - 1], _gf_mul(_gen[j], alpha_i));
            }
            _gen[0] = _gf_mul(_gen[0], alpha_i);
        }
    }

    // ── Systematic encoder ──
    void _encode_block(const uint8_t* msg, uint8_t* codeword) const {
        const_cast<ReedSolomon*>(this)->_init_gen();
        std::memcpy(codeword, msg, K);
        std::memset(codeword + K, 0, NPAR);
        uint8_t parity[NPAR]{};
        for (int i = 0; i < K; ++i) {
            uint8_t fb = _gf_add(msg[i], parity[0]);
            for (int j = 0; j < NPAR - 1; ++j) {
                parity[j] = _gf_add(parity[j + 1], _gf_mul(fb, _gen[NPAR - 1 - j]));
            }
            parity[NPAR - 1] = _gf_mul(fb, _gen[0]);
        }
        std::memcpy(codeword + K, parity, NPAR);
    }

    // ── Syndrome calculation ──
    void _calc_syndromes(const uint8_t* codeword, uint8_t* syn) const {
        bool all_zero = true;
        for (int i = 0; i < NPAR; ++i) {
            uint8_t s = 0;
            uint8_t alpha_i = _exp[i];
            uint8_t term = 1;
            for (int j = 0; j < N; ++j) {
                s ^= _gf_mul(codeword[j], term);
                term = _gf_mul(term, alpha_i);
            }
            syn[i] = s;
            if (s != 0) all_zero = false;
        }
        if (all_zero) {
            syn[0] = 0;  // signal: no errors
        }
    }

    // ── Berlekamp-Massey algorithm ──
    int _berlekamp_massey(const uint8_t* syn, uint8_t* sigma, int /*max_deg*/) const {
        uint8_t b[NPAR + 1]{};
        uint8_t old_sigma[NPAR + 1]{};
        sigma[0] = 1;
        b[0] = 1;
        int L = 0;
        int m = 1;
        uint8_t b_inv = 1;

        // Check if all syndromes are zero
        bool all_zero = true;
        for (int i = 0; i < NPAR; ++i) {
            if (syn[i] != 0) { all_zero = false; break; }
        }
        if (all_zero) { sigma[0] = 1; return 0; }

        for (int r = 0; r < NPAR; ++r) {
            // Compute discrepancy δ_r
            uint8_t delta = syn[r];
            for (int j = 1; j <= L; ++j) {
                delta ^= _gf_mul(sigma[j], syn[r - j]);
            }

            if (delta == 0) {
                ++m;
            } else {
                uint8_t delta_b_inv = _gf_mul(delta, b_inv);
                // Save old sigma
                for (int i = 0; i <= NPAR; ++i) old_sigma[i] = sigma[i];

                // sigma(x) = sigma(x) - δ·b_inv·x^m·b(x)
                for (int i = 0; i <= NPAR; ++i) {
                    if (i + m <= NPAR) {
                        sigma[i + m] ^= _gf_mul(delta_b_inv, b[i]);
                    }
                }

                if (2 * L <= r) {
                    L = r + 1 - L;
                    for (int i = 0; i <= NPAR; ++i) b[i] = old_sigma[i];
                    b_inv = _gf_inv(delta);
                    m = 1;
                } else {
                    ++m;
                }
            }
        }
        return L;
    }

    // ── Chien search ──
    int _chien_search(const uint8_t* sigma, int deg, uint8_t* positions) const {
        int count = 0;
        for (int i = 0; i < N && count < deg; ++i) {
            uint8_t val = 1;
            uint8_t alpha_i = _exp[i];  // α^i, evaluating at x = α^(-i)
            uint8_t term = 1;
            for (int j = 1; j <= deg; ++j) {
                term = _gf_mul(term, alpha_i);
                val ^= _gf_mul(sigma[j], term);
            }
            if (val == 0) {
                positions[count++] = static_cast<uint8_t>(N - 1 - i);
            }
        }
        return count;
    }

    // ── Forney algorithm for error values ──
    void _forney(const uint8_t* syn, const uint8_t* sigma, int deg,
                 const uint8_t* positions, int nerr, uint8_t* values) const {
        // Compute error evaluator polynomial Ω(x) = S(x)·σ(x) mod x^(2T)
        uint8_t omega[NPAR]{};
        for (int i = 0; i < NPAR; ++i) {
            omega[i] = syn[i];
            for (int j = 1; j <= deg && j <= i; ++j) {
                omega[i] ^= _gf_mul(sigma[j], syn[i - j]);
            }
        }

        // Compute σ'(x) (formal derivative = odd terms)
        uint8_t sigma_deriv[NPAR]{};
        for (int i = 1; i <= deg; i += 2) {
            sigma_deriv[i - 1] = sigma[i];
        }

        for (int k = 0; k < nerr; ++k) {
            uint8_t pos = positions[k];
            uint8_t x_inv = _exp[(N - 1 - pos) % 255];  // α^(-pos)

            // Evaluate Ω(x_inv)
            uint8_t omega_val = 0;
            uint8_t term = 1;
            for (int j = 0; j < NPAR; ++j) {
                omega_val ^= _gf_mul(omega[j], term);
                term = _gf_mul(term, x_inv);
            }

            // Evaluate σ'(x_inv)
            uint8_t deriv_val = 0;
            uint8_t dterm = 1;
            for (int j = 0; j < NPAR; ++j) {
                deriv_val ^= _gf_mul(sigma_deriv[j], dterm);
                dterm = _gf_mul(dterm, x_inv);
            }

            values[k] = _gf_mul(omega_val, _gf_inv(deriv_val));
        }
    }

    // ── Full decoder for one block ──
    bool _decode_block(const uint8_t* codeword, uint8_t* msg) const {
        // Copy message portion first (will be corrected in-place)
        std::memcpy(msg, codeword, K);

        uint8_t syn[NPAR];
        _calc_syndromes(codeword, syn);

        // Check if all syndromes are zero → no errors
        bool all_zero = true;
        for (int i = 0; i < NPAR; ++i) {
            if (syn[i] != 0) { all_zero = false; break; }
        }
        if (all_zero) {
            _last_corrected = 0;
            return true;
        }

        // Berlekamp-Massey
        uint8_t sigma[NPAR + 1]{};
        int L = _berlekamp_massey(syn, sigma, NPAR);
        if (L == 0 || L > T) {
            _last_corrected = -1;
            return false;  // uncorrectable
        }

        // Chien search
        uint8_t positions[T];
        int nerr = _chien_search(sigma, L, positions);
        if (nerr != L) {
            _last_corrected = -2;
            return false;
        }

        // Forney algorithm
        uint8_t values[T];
        _forney(syn, sigma, L, positions, nerr, values);

        // Correct errors in the message portion
        _last_corrected = 0;
        for (int k = 0; k < nerr; ++k) {
            if (positions[k] < K) {
                msg[positions[k]] ^= values[k];
                ++_last_corrected;
            }
        }
        return true;
    }
};

#endif // REED_SOLOMON_HPP

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
