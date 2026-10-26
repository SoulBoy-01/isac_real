# 小论文投稿指南（SCI 3–4 区方向）

> 配套文件：`manuscript_sci_v1.md`（英文投稿版）、`manuscript_zh_v1.md`（中文版）。
> 更新日期：2026-10-04。**分区/费用为大致情况，投稿前务必在 LetPub 或最新中科院分区表核实。**

## 一、候选期刊（按推荐顺序）

| # | 期刊 | 出版商 | 分区（约） | 首决速度 | 匹配度 | 费用（约） |
|---|---|---|---|---|---|---|
| 1 | **IEEE Access** | IEEE | JCR Q1–Q2 / 中科院 3 区 | **快（1–2 月）** | ★★★★★ 跨层实验类文章的标准去处，篇幅不限 | OA 约 $2,045 |
| 2 | **Sensors / Electronics** | MDPI | Q2 / Q2–Q3 | **最快（4–7 周）** | ★★★★☆ 范围匹配；注意学校对 MDPI 的认可政策 | OA 约 2,400–2,600 CHF |
| 3 | **IET Communications** | Wiley(IET) | Q3–Q4 | 中（3–6 月） | ★★★★☆ 物理层+系统实验的经典去处 | OA 约 £2,200 |
| 4 | **EURASIP J. Wireless Commun. Netw.** | Springer | Q3 | 中 | ★★★★☆ 无线网络+实验，口碑正常 | OA（见官网） |
| 5 | **Wireless Personal Communications** | Springer | Q3–Q4 / 中科院 4 区 | 慢（6–12 月） | ★★★☆☆ 工程实验传统刊；可选订阅制（免费） | 订阅制可 0 费用 |
| 6 | **Telecommunication Systems** | Springer | Q3–Q4 | 慢 | ★★★☆☆ 同上 | 订阅制可 0 费用 |
| 7 | **Physical Communication** | Elsevier | Q3–Q4 | 中 | ★★★☆☆ 更偏物理层（RS/LDPC/CP 实验契合） | 可订阅制 |

**推荐策略**：预算允许 → IEEE Access（范围最匹配、速度最快、审稿意见通常可执行）；预算敏感 → Wireless Personal Communications 或 Telecommunication Systems 走订阅制免费路线；求最快见刊 → MDPI，但**先确认学校学位/职称文件是否认可 MDPI**（部分单位有白名单）。

⚠️ 投稿前必查：① 最新中科院分区表（每年升级）；② 学校研究生院认可的期刊目录（专硕毕业要求通常对目录有明确限定）。

## 二、投稿前检查清单

- [ ] 填写作者、单位、通讯作者、基金（`manuscript_sci_v1.md` 顶部与声明区）
- [ ] 图 1/4（AI 辅助示意图）：投稿信中主动披露；或用 matplotlib 重绘矢量版
- [ ] 图 2/3/5 数据图：camera-ready 换 `*_mpl` 矢量版（改文件名即可）
- [ ] 补 γ 压力测试时的精确 BER 工作点（审稿人可能问）
- [ ] 准备 3 位建议审稿人（ISAC/SDR 方向，无合作历史）
- [ ] 查重（自引先前工作仅 OpenISAC 平台论文，无重复发表问题）

## 三、Cover Letter 模板（以 IEEE Access 为例）

> Dear Editor-in-Chief,
>
> We are pleased to submit our manuscript entitled "Cross-Layer Design and Experimental Evaluation of Real-Time H.264 Video Transmission over an Open-Source OFDM-ISAC Platform" for consideration in IEEE Access.
>
> While ISAC testbeds are maturing rapidly, published evaluations overwhelmingly target sensing accuracy or link-level throughput; how a *continuous media service* actually behaves on such a link has not been measured. Using the open-source OpenISAC platform over a live USRP link, we instrument every layer of a real-time H.264 video service and report three quantitative findings: (i) the lightest Reed–Solomon outer code is already sufficient, as the measured LDPC residual BER is below 5×10⁻¹⁰; (ii) MPEG-TS containerization amplifies the effective packet-failure probability by 7× (model) and 4×–500× (measured across decoders), which motivates a bare-H.264 transport design; and (iii) queue restructuring pins end-to-end latency at 250 ± 0.5 ms, ~80% of which belongs to the decoder rather than the radio. These results condense into a least-sufficient-protection design rule of practical value for ISAC system builders.
>
> All experiments were conducted on publicly available hardware and an open-source platform; configurations and measurement procedures are fully documented in the paper for reproducibility. This manuscript is original, has not been published previously, and is not under consideration elsewhere. All authors have approved the submission.
>
> We believe this work falls squarely within the scope of IEEE Access. Thank you for your consideration.
>
> Sincerely,
> [Corresponding Author], on behalf of all authors
> [Affiliation, email]

## 四、中文期刊备选（如走中文路线）

`manuscript_zh_v1.md` 可改投科技核心/中文核心（如《无线电通信技术》《电讯技术》《无线电工程》《数据采集与处理》等，均收 OFDM/SDR 实验类文章）。**注意**：中文版同时是大论文第 3–6 章的底稿，若计划学位论文后再投中文期刊，注意学校对"学位论文内容再发表"的规定；英文 SCI 版无此顾虑（语言不同+已标注学位论文支撑）。
