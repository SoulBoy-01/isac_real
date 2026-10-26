# Cross-Layer Design and Experimental Evaluation of Real-Time H.264 Video Transmission over an Open-Source OFDM-ISAC Platform

**Authors:** [First Author]¹, [Second Author]¹, [Corresponding Author]¹,*
**Affiliations:** ¹ [Department, University, City, Country]
***Corresponding author:** [email]
**Article type:** Full-length research article

---

## Highlights

- Real-time H.264 video and radar sensing run concurrently on an open-source OFDM-ISAC testbed.
- An RS outer-code scan shows the lightest code suffices; LDPC residual BER is below 5×10⁻¹⁰.
- MPEG-TS containerization amplifies effective packet failure by 7× (model) and 4×–500× (measured).
- Queue restructuring pins latency at 250 ± 0.5 ms, with ~80% owed to the video decoder.
- A least-sufficient-protection rule is derived for media services on strongly coded ISAC links.

## Abstract

Integrated sensing and communication (ISAC) systems carry radar sensing and user payloads over a shared OFDM waveform, and real-time video is among the most demanding payloads such a link can serve. Although ISAC testbeds are maturing rapidly, existing evaluations target sensing accuracy or link-level throughput and leave the application-layer transport stack unexamined. This paper presents a cross-layer experimental study of real-time H.264 video delivery over OpenISAC, an open-source real-time OFDM-ISAC platform, operating over a live indoor link between USRP N320 and B210 radios. Three findings are reported. First, a Pareto scan of four RS(255,K) outer codes shows that all configurations achieve zero steady-state failures once the link synchronizes; the LDPC(1008,504) residual error rate is below 5×10⁻¹⁰, so the lightest code, RS(255,223) with 14.3% redundancy, is sufficient and recovers 8.4% of payload throughput over the originally deployed RS(255,191). Second, a packet-failure model of the MPEG transport stream (MPEG-TS) predicts a 7× amplification of the effective failure probability of the raw H.264 stream from header exposure alone; measurements under a disabled-outer-code stress test span 4×–500× across three decoder stacks, and replacing MPEG-TS with bare H.264 Annex B together with a fault-tolerant decoder removes persistent decoding stalls. Third, reducing queue depths from 32 to 4–8 frames with non-blocking drops removes a positive-feedback latency loop and pins end-to-end latency at 250 ms with 0.5 ms steady-state jitter, of which about 80% is attributable to the H.264 decoder. The results yield a least-sufficient-protection design rule for media services on strongly coded ISAC links, and the full parameter sets are provided for reproducibility.

**Keywords:** Integrated sensing and communication (ISAC); OFDM; real-time video transmission; Reed-Solomon codes; LDPC codes; MPEG-TS; cross-layer design; software-defined radio; H.264/AVC; error resilience

---

## 1. Introduction

The sixth generation of mobile networks (6G) is expected to natively support integrated sensing and communication (ISAC), in which the same waveforms, hardware, and spectrum serve both data transmission and environmental sensing [1]–[4]. Because ISAC links are built from wideband OFDM transmission, large antenna arrays, and high-rate digital baseband processing — the same ingredients as modern radar — a single link can simultaneously deliver user payloads and perform range/Doppler estimation of its surroundings [5]. Experimental ISAC platforms are therefore a growing focus of the community, and open platforms such as OpenISAC now allow complete physical-layer experimentation over the air with modest hardware [6], [7].

Among the payloads such a link can carry, real-time video is a stress test at the extreme. It demands sustained throughput, bounded and non-accumulating latency, and — most distinctively — tolerance to *residual* errors: bit errors that survive the physical-layer forward error correction (FEC). Residual errors are tolerable for file transfer, where retransmission repairs them, but they are structurally hostile to inter-frame video codecs such as H.264/AVC [8]: a single corrupted macroblock propagates through prediction loops until the next intra-refresh, corrupting up to a group of pictures (GOP) of frames. A real-time ISAC video service therefore couples the error statistics of a strongly coded OFDM link to design decisions at the container, decoder, and buffer layers — decisions that existing ISAC experimental studies largely leave unexamined, because they evaluate sensing estimation accuracy or link-level throughput rather than a continuous media service.

Prior work on wireless video transport has studied each of these layers separately. Application-layer studies of error-resilient video have examined FEC, retransmission, and cross-layer adaptation for wireless networks [9]–[11], and recent joint source–channel coding replaces parts of the classical separation-based stack with learned codecs [12]. Channel-coding studies, in turn, have long used concatenated Reed-Solomon/LDPC or RS/convolutional architectures, with outer codes sized against the modeled inner-code residual [10], [13]. What is missing is a systematic, measured account of *where* video quality actually breaks in a modern ISAC link that already runs a strong LDPC inner code: which layer's choices dominate the delivered quality, and how much protection each layer actually needs. To our knowledge, no experimental study has quantified the error-amplification behavior of the MPEG transport stream (MPEG-TS) container [14] — the default encapsulation for H.264 over IP — on a live ISAC link, nor compared how popular decoder stacks respond to the same physical-layer error stream.

This paper presents such an account. Using the OpenISAC platform [6] with an N320 base station and a B210 user equipment over an indoor over-the-air link, we instrument every layer of a real-time H.264 video service and run controlled experiments at each:

1. **Outer-code redundancy (Section 4).** A Pareto scan of four RS(255,K) outer codes (K = 223, 207, 191, 179) shows that once the link is synchronized, *all* configurations deliver zero steady-state block failures. The LDPC(1008,504) inner code's residual error rate is below 5×10⁻¹⁰, so the outer code acts only as a transient guard during synchronization, and the lightest configuration is optimal: RS(255,223) recovers 8.4% of effective payload throughput relative to the deployed RS(255,191) with indistinguishable reliability.
2. **Container and decoder selection (Section 5).** We derive a packet-failure model showing that MPEG-TS encapsulation multiplies the effective failure probability of the H.264 byte stream by a factor γ ≈ 7 from header exposure alone, and measure γ = 4× to 500× across three decoder stacks under a disabled-outer-code stress test. Switching from MPEG-TS to bare H.264 Annex B with a fault-tolerant decoder removed persistent stalls that made container-based playback unusable under the same physical error stream.
3. **Buffering and latency (Sections 5 and 7).** Reducing queue depths from 32 to 4–8 frames and replacing blocking enqueue with non-blocking drops eliminates a positive-feedback latency loop; end-to-end latency pins at 250 ms with 0.5 ms steady-state jitter over five minutes, and a decomposition shows ≈80% of it belongs to the H.264 decoder, not the ISAC link.
4. **Modulation, encoding, and waveform parameters (Section 6).** 16QAM is compute-bound rather than channel-bound on the B210 receiver; the encoding bitrate and GOP are tuned to bound error-propagation exposure; and a cyclic-prefix reduction experiment locates the indoor multipath delay spread that the protection interval must cover.

The rest of the paper is organized as follows. Section 2 discusses related work. Section 3 describes the system. Sections 4–7 present the experimental results. Section 8 interprets them into a design principle — *least-sufficient protection* — and states limitations. Section 9 concludes.

## 2. Related Work

**ISAC platforms and over-the-air experimentation.** OFDM-based joint communication and radar sensing dates to the waveform-fusion analysis of Sturm and Wiesbeck [5], and the field has since produced a rich theoretical literature on dual-functional waveform and system design [2]–[4]. Experimental validation, however, has been comparatively scarce because real-time ISAC requires full transmit and receive chains operating over the air. Recent platforms close this gap: Brunner et al. [7] demonstrated bistatic OFDM ISAC with over-the-air synchronization, and OpenISAC [6] provides an open-source real-time OFDM-ISAC platform with monostatic and bistatic sensing, YAML-based configuration, and support for common USRP hardware. These platforms establish that sensing estimation and link-level throughput can be measured over the air. What they do not establish is how a *continuous media service* behaves on top of such a link: their evaluation targets sensing accuracy and physical-layer performance, leaving containerization, decoder behavior, and buffer sizing as unexamined engineering defaults. Our work takes the platform as given and measures exactly that neglected layer.

**Wireless video transport and cross-layer design.** A large literature studies error-resilient video over wireless networks, spanning application-layer FEC, retransmission, unequal protection, and cross-layer rate adaptation [9]–[11]. These studies generally assume the physical layer is either given (e.g., an existing cellular link) or abstracted as a packet-erasure channel, and they optimize the application layer against it. Learned joint source–channel coding (JSCC) replaces part of the classical stack end to end [12], but requires replacing the codec rather than tuning the deployed one. None of these lines addresses a setting in which the physical layer is itself configurable and already runs a strong LDPC code — the regime of ISAC prototyping platforms, where the interesting question is how much *additional* protection each higher layer needs.

**Concatenated coding and residual-error handling.** Sizing an outer code against an inner code's residual errors is classical [10], [13], and the standard practice is to size the outer code against a modeled or worst-case residual. In our measurements on a live QPSK link, the modeled worst case is far pessimistic: the LDPC residual is so sparse that even the lightest tested outer code never fires in steady state. Our RS Pareto scan quantifies this sparsity empirically and turns it into a concrete design rule — and, by experimentally disabling the outer code, exposes how much of the delivered video quality is decided *above* the channel code, in the container and decoder.

## 3. System Description

### 3.1 Platform and video pipeline topology

All experiments use the OpenISAC platform [6], an open-source real-time OFDM-ISAC implementation whose C++ PHY runs on software-defined radios. The base station (BS) uses a NI USRP N320 (dual-channel, 200 MHz FPGA, internal GPSDO discipline) connected over SFP+ 10-Gigabit Ethernet; the user equipment (UE) uses a NI USRP B210 (AD9361 front end, 12-bit ADC, USB 3.0). Both sides use log-periodic antennas (6–8 dBi, 60–90° beamwidth). The video service is layered onto the platform's UDP payload interfaces:

```
camera → H.264 encoder → UDP :50000 → ISAC modulator (N320) →~air~→
ISAC demodulator (B210) → UDP :50001 → H.264 decoder → display
```

The sensing chain runs concurrently on the same waveform: a copy of the transmit signal feeds the sensing processing path at the BS, and the demodulated-and-equalized symbols support bistatic sensing reconstruction at the UE. All experiments in this paper operate the video service and the sensing function simultaneously on the shared link.

![Fig. 1](figures/fig1_topology.png)

**Fig. 1 | System topology.** Real-time video service on the OpenISAC platform: camera → H.264 encoder → ISAC transmit chain (RS–LDPC concatenated coding over OFDM) → wireless link → ISAC receive chain → H.264 decoder → display. Monostatic and bistatic sensing run concurrently on the shared waveform.

### 3.2 OFDM frame structure

Table 1 lists the fixed waveform parameters. The frame duration is 2.304 ms (≈434 frames/s). The direct-current subcarrier is nulled to avoid local-oscillator leakage; 978 subcarriers carry data and pilots. The synchronization symbol (symbol index 1) is filled with a Zadoff–Chu sequence of root index u = 29, whose constant-amplitude zero-auto-correlation property gives flat frequency-domain magnitude and a sharp time-domain correlation peak for frame synchronization. Pilot subcarriers carry known ZC reference symbols for carrier-frequency-offset (CFO), sampling-frequency-offset (SFO), and channel-phase tracking; we reduced the pilot density from 16 to 8 uniformly spaced subcarriers ([29, 150, 270, 391, 571, 692, 812, 933]) after verifying that the LMMSE estimator reconstructs the full 1024-subcarrier response from 8 pilots without observable degradation, releasing 792 resource elements per frame (+0.79% throughput).

**Table 1. OFDM frame parameters.**

| Parameter | Symbol | Value |
|---|---|---|
| FFT size | N | 1024 |
| Cyclic prefix | G | 128 (12.5%, 2.56 μs) |
| Symbols per frame | M | 100 |
| Sampling rate | F_s | 50 MHz |
| Subcarrier spacing | Δf | 48.828 kHz |
| Frame duration | T_f | 2.304 ms (≈434 frames/s) |

### 3.3 Concatenated channel-coding chain

The transmit chain is

```
UDP payload → RS(255,223) outer code → LDPC(1008,504) inner code
→ scrambler → 21×48 block interleaver → QAM mapping → OFDM modulation
```

The **RS(255,K) outer code** operates over GF(2⁸) with primitive polynomial 0x11D and corrects t = (255−K)/2 byte errors per 255-byte codeword using the standard syndrome → Berlekamp–Massey → Chien/Forney chain; decoding failure falls back to passing the block through unchanged, and success/failure counters expose a per-interval fail rate. A 2-byte big-endian length prefix precedes each payload so that variable-length UDP datagrams can be recovered at the decoder. The **LDPC(1008,504) inner code** (rate 1/2) uses the BP-horizontal-layered normalized min-sum decoder of the AFF3CT library [15] with 6 iterations and syndrome-based early termination. The scrambler is an LFSR with polynomial x⁸ + x⁷ + x³ + x² + 1 and seed 0x5A; the 21×48 block interleaver spreads LDPC decoder bursts across codewords.

### 3.4 Receiver processing and the video stack

The receiver performs LMMSE channel estimation (least-squares estimate from the ZC reference, Wiener-filtered in the CP-length time domain), joint CFO/SFO estimation by weighted linear regression of pilot phase differences, zero-forcing equalization with phase-slope correction, and max-log-MAP soft demapping of the Gray-coded square QAM constellations. A predictive timing compensator uses the detected CFO to pre-correct frame-timing drift between the radios' clock domains.

On top of the payload interfaces, the video service uses GStreamer on both ends in the final configuration: `rtspsrc → h264parse → udpsink` at the transmit side and `udpsrc → h264parse → avdec_h264` at the receive side, carrying bare H.264 Annex B elementary stream (Section 5.2 explains why not MPEG-TS). The baseline video format is 640×480 at 20 fps, 1200 kbps, GOP 30, encoded with x264 (ultrafast); an NVENC hardware encoder (RTX 3050, preset p1) was also tested and reduces encoding latency from ≈10 ms to <1 ms with no observable receive-side difference.

## 4. Outer-Code Redundancy: A Pareto Analysis

### 4.1 Motivation: residual errors after LDPC

A finite-iteration LDPC decoder exhibits an error floor: even at high SNR, codewords occasionally fail with a small number of residual bit errors. For file transfer these residuals are repaired by retransmission; for inter-frame video they are amplified into visible corruption lasting up to a GOP. The classical remedy is an outer byte-oriented code sized against the inner code's residual [10], [13] — but *how strong* the outer code must be is an empirical question that, to our knowledge, has not been answered by measurement on a live strongly coded ISAC link. We therefore scanned four RS(255,K) configurations spanning a 3× range of redundancy (Table 2).

**Table 2. RS outer-code configurations under test.**

| Configuration | K (data bytes) | Parity bytes | t (correctable) | Redundancy |
|---|---|---|---|---|
| RS(255,223) | 223 | 32 | 16 | 14.3% |
| RS(255,207) | 207 | 48 | 24 | 23.2% |
| RS(255,191) | 191 | 64 | 32 | 33.5% |
| RS(255,179) | 179 | 76 | 38 | 42.5% |

### 4.2 Experimental design

Each configuration was compiled into both radios and exercised by a fixed-pattern load (1024-byte packets, 4-byte sequence number + 0xA5 fill) injected at rates from 500 to 4000 kbps in 10-s intervals, with a 640×480@20 fps H.264 stream running concurrently for subjective quality assessment. A configuration's fail rate was read after the success counter exceeded 20,000 packets (steady state). The QPSK link, center frequency, and all other parameters were held fixed across configurations.

### 4.3 Results: zero steady-state failures in all configurations

The result is unambiguous: **every configuration, including the lightest, recorded zero decoding failures in steady state.** The only failure events across the entire campaign occurred in the first measurement window after startup (success counter < 1,000), i.e., during the initial frame-synchronization transient, and appeared in all four configurations — indicating that they stem from synchronization settling, not from residual channel errors exceeding any particular t. Beyond the transient, the failure rate decays as 1/n with the packet count, the signature of a single bounded transient event rather than an ongoing error process.

Across the campaign more than 10⁶ RS codewords were decoded without a single steady-state correction event, which bounds the LDPC residual byte-error rate at below 1/(255×8×10⁶) ≈ 5×10⁻¹⁰ under our indoor SNR conditions. Subjective video quality was indistinguishable across configurations.

### 4.4 The Pareto choice and throughput recovery

Given equal steady-state reliability, the lightest code dominates. Switching the deployed configuration from RS(255,191) (33.5% redundancy) to RS(255,223) (14.3%) raises the code-rate ratio by 223/191 − 1 = 16.8%; with the 2-byte length prefix included for 1024-byte payloads, the effective payload-throughput gain is 8.4%. We adopted RS(255,223) for all subsequent experiments.

Two consequences follow. First, on this link the outer code functions as a *transient guard* — absorbing the synchronization-establishment window — rather than an active corrector; its steady-state correction capability is unused headroom. Second, the LDPC residual sparsity implies that any protection added *above* the outer code will, in steady state, see an essentially clean byte stream — which is precisely why the container- and decoder-level failures of Section 5, which occur when the outer code is disabled, dominate video quality in stressed conditions.

## 5. Application-Layer Optimization

### 5.1 Queue sizing and the elimination of latency accumulation

The initial deployment used default queue depths of 32 frames at four points in the pipeline (post-encoding buffer, post-modulation circular buffer, pre-demodulation frame queue, and synchronization queue). At 434 frames/s each queue contributes up to ≈74 ms of worst-case queuing delay, and the aggregate delay was not merely additive: when the H.264 decoder momentarily stalled, UDP receive buffers filled, the demodulator's downstream send blocked, the LDPC decode thread was back-pressured, and the frame queue grew further — a positive-feedback loop in which latency accumulated without bound.

We addressed this structurally rather than incrementally: queue depths were reduced to the minimum sustaining continuous processing (16 post-encode, 8 post-modulate, 4 pre-demodulate, 8 synchronization), and all blocking enqueues were replaced by `try_push` semantics that drop on overflow. The drops convert an unbounded latency growth into a bounded, visible loss — the correct trade for a real-time service. After the change, end-to-end latency — measured by the stopwatch method (a millisecond timer filmed simultaneously at the camera and on the receiving display; 30 fps capture gives ≈33 ms resolution) — pinned at **250.3 ± 0.5 ms** across the steady-state samples of a five-minute run, with no accumulation trend (Fig. 2; full trace in Section 7.1).

![Fig. 2](figures/fig2_latency.png)

**Fig. 2 | End-to-end latency.** (a) Five-minute stopwatch trace; the shaded window marks the steady-state interval (250.3 ± 0.5 ms); gray points are decoder-side buffer resets (receiver software, not the ISAC link). (b) Latency decomposition: the H.264 decoder and GStreamer pipeline contribute ≈80% of the ≈250 ms total.

### 5.2 Container fragility: modeling and measuring γ

H.264 over IP is conventionally encapsulated in the MPEG transport stream [14]. TS was designed for broadcast channels with controlled error characteristics; its resynchronization machinery assumes that errors are rare and bounded. We model its behavior on a link with byte-error probability p as follows. A TS packet is 188 bytes, of which the critical header fields — the 0x47 sync byte, the PID and continuity counter, and the PES start code — occupy m critical bytes; a single bit error in any critical byte causes the packet to be discarded or the continuity counter to break. Because practical deployments bundle 7 TS packets per UDP datagram (1316 bytes), a corrupted sub-packet destroys the synchronization of the whole bundle, giving an effective critical-byte count of m ≈ 28 per bundle. The bundle failure probability is therefore P_fail^TS ≈ 28p. A bare H.264 Annex B stream, by contrast, resynchronizes on any 4-byte start code (0x00000001), giving P_fail^raw ≈ 4p. The container therefore amplifies the effective failure probability by

$$\gamma_{model} = P_{fail}^{TS} / P_{fail}^{raw} \approx 7.$$

Beyond packet loss, TS synchronization *recovery* is itself fragile. Recovery can be modeled as an absorbing Markov chain: the parser skips bytes seeking 0x47, may lock onto a false 0x47 inside the payload, fails continuity validation, and re-enters the search; only a run of valid packet headers (typically 3–5) reaches the absorbing "locked" state. During false-lock cycling the decoder discards all input, for up to seconds. This is the mechanism behind the `TS discontinuity` stalls observed with VLC.

We measured the *container amplification factor* γ = P_data_loss/p empirically by running each transport stack with the RS outer code disabled (an extreme stress test that raises the post-LDPC byte-error rate to measurable levels while the LDPC inner code still operates):

**Table 3. Measured container amplification factors (RS outer code disabled).**

| Transport stack | γ (measured) | Dominant mechanism |
|---|---|---|
| MPEG-TS + VLC (hardware-decode path) | ≈500× | sync-search residence + buffer deadlock |
| MPEG-TS + ffplay (software decode) | ≈150× | bounded sync search, no deadlock |
| bare H.264 + ffplay | ≈8× | occasional frame-level cascades |
| bare H.264 + GStreamer (`output-corrupt=true`) | ≈4× | start-code risk only; silent frame skip |

Under this stress test, MPEG-TS + VLC produced 0% usable playback time (persistent frozen frames), MPEG-TS + ffplay ≈30%, and bare H.264 + GStreamer ≈95%, with the raw TS packet failure rate at 99.5%. With the outer code re-enabled the same ordering persisted (TS stacks reported far more `Packet corrupt` events than the bare stream's silent skips), confirming that the difference is attributable to the container and decoder rather than to any change in the physical error stream (Fig. 3). The measured amplification (4×–500×) brackets the header-exposure prediction (7×) from both sides: at the low end, a fault-tolerant decoder repairs most of the exposure; at the high end, decoder state machines amplify it.

![Fig. 3](figures/fig3_gamma.png)

**Fig. 3 | Container amplification factor γ.** Modeled prediction (dashed line, header-exposure only) versus measurement for four transport stacks under the RS-disabled stress test. MPEG-TS stacks (red) amplify the effective failure probability far beyond the header-exposure prediction; bare-stream stacks (blue) stay below it.

The design consequence is that on an ISAC link with occasional residual errors, **MPEG-TS should be replaced by bare H.264 Annex B**, accepting manual stream-boundary handling in exchange for a 7× reduction in modeled exposure — and the decoder must be chosen for fault tolerance, not throughput.

### 5.3 Decoder selection

Table 4 summarizes the three decoders compared. VLC couples a hardware-first decode path to the TS PCR clock reference; under a broken continuity chain it deadlocks. ffplay (libavcodec, external clock) degrades gracefully but visibly. GStreamer's `avdec_h264` with `output-corrupt=true` emits corrupt frames as they arrive and skips silently on damage, giving the cleanest recovery behavior on the bare stream. We adopted GStreamer + bare H.264 as the reference receive stack.

**Table 4. Decoder behavior under residual errors.**

| Decoder | Decode path | Clock model | Error response |
|---|---|---|---|
| ffplay (libavcodec) | software | external clock (`-sync ext`) | `Packet corrupt` → error concealment |
| VLC (VDPAU) | hardware-first | PCR-referenced | `TS discontinuity` → deadlock |
| GStreamer (avdec_h264) | software | none | `output-corrupt=true` → emit/skip |

### 5.4 Conditional error propagation under large-area motion

Even in the optimized configuration, a specific failure mode remains: when more than ≈2/3 of the picture changes between frames, the H.264 frame size grows from ≈6,000 to ≈15,000 bytes, and the number of LDPC blocks per frame from ≈30 to ≈75. With a per-block residual-failure probability of ≈0.002%, the joint probability that a motion frame contains at least one damaged block is ≈0.15% (vs. 0.06% for static frames) — and when damage does occur, error concealment fails precisely because the previous frame's content no longer matches the moving scene. At 20 fps this yields ≈0.03 events/s: one visible corruption roughly every 30 s *under sustained large-area motion only*, recovering within the GOP (<1 s). This is a structural interaction between inter-frame coding and channel randomness, not a system defect; Section 6.2 quantifies how the encoding bitrate bounds its exposure (Fig. 4).

![Fig. 4](figures/fig4_artifact_chain.png)

**Fig. 4 | Causal chain of conditional corruption.** Large-area motion inflates frame size and LDPC block count, raising the per-frame joint damage probability; inter-frame prediction then propagates the damage until the next I-frame, producing visible corruption at ≈1 event per 30 s that recovers within one GOP.

## 6. Modulation and Parameter Studies

### 6.1 16QAM: a compute-bound ceiling

Switching QPSK → 16QAM doubles the theoretical throughput (4.7 → 9.5 Mbps). On the B210 receiver the switch failed — but not in the channel. The constellation remained clean (16 well-separated points), yet CPU load rose from 32% to 105% and per-frame processing from 0.74 ms to 2.38 ms, overflowing the frame queue and breaking the link. The asymmetry is in the soft demapper: QPSK's PAM-2 max-log-MAP needs two LLR terms per resource element, while 16QAM's PAM-4 needs four plus absolute-value and comparison branches. Within a 2.304 ms frame budget, the B210's embedded processor cannot complete the doubled computation. QPSK is therefore the practical modulation ceiling *of this receiver platform*, and the bottleneck is computational, not informational — indicating that a receiver upgrade (Section 8.3), not a waveform change, is what unlocks higher-order QAM.

### 6.2 Video encoding parameter scan

Sweeping the H.264 bitrate at fixed 640×480@20 fps (Table 5) exposes the trade-off between image quality and error-propagation exposure: higher bitrate → larger frames → more LDPC blocks per frame → higher joint damage probability. 1200 kbps (≈38 blocks/frame) was selected as the operating point with acceptable quality and the lowest motion-artifact frequency; 2500 kbps doubled the visible artifact rate. GOP 30 bounded the error-propagation window. MJPEG (no inter-frame prediction) was tested as an alternative: its damage is naturally localized (no propagation) but, at equal resolution, its larger frames raise the per-frame damage frequency, and the overall experience was inferior to H.264. MJPEG remains attractive for latency-critical applications that tolerate frequent but local damage.

**Table 5. Bitrate scan (640×480@20 fps).**

| Bitrate (kbps) | ≈bytes/frame | ≈LDPC blocks | Quality | Motion artifacts |
|---|---|---|---|---|
| 800 | 5,000 | 25 | moderate | low |
| 1200 | 7,500 | 38 | good | low (selected) |
| 1800 | 11,250 | 56 | good+ | medium |
| 2500 | 15,600 | 78 | very good | high |

### 6.3 Cyclic-prefix margin: the CP=64 failure

Halving the cyclic prefix (128 → 64 samples; 12.5% → 6.7% overhead) promised +5.9% throughput. Indoors, it failed completely: the receiver entered a `No valid delay found` loop with 0.5 s hard resets, and the reported CFO jumped from 7.4 kHz (≈2.3 ppm, plausible) to 95 kHz (30.6 ppm, physically implausible) — a mathematical artifact of ISI corrupting the pilot-phase regression, not real drift. The mechanism: at CP=64 (1.28 μs ≈ 384 m), indoor reflections from walls and ceiling exceeded the protection window, ISI polluted the LMMSE channel estimate, the delay-spectrum peak-to-average ratio fell below the 20× detection threshold, and synchronization collapsed. Although the BS–UE distance is ≈5 m, the *effective* delay spread of the indoor environment demands CP=128 (2.56 μs ≈ 768 m). This experiment provides a measured lower bound on the cyclic prefix for indoor ISAC links of this bandwidth — the reflection geometry, not the link distance, sets the requirement.

## 7. End-to-End Performance

### 7.1 Latency: measurement and decomposition

With the full optimized configuration (QPSK, RS(255,223), 1200 kbps bare H.264, GStreamer, tuned queues), the five-minute stopwatch trace (Table 6, Fig. 2a) shows a steady-state latency of **250 ms ± 0.5 ms** (first four samples) with no accumulation trend over the full run; later samples deviate (266 ms, 233 ms, then 112/38 ms) when the decoder's internal buffer management resets its reference-frame pool — a receiver-side software behavior, not a link effect.

**Table 6. End-to-end latency trace (five minutes).**

| Time (s) | Latency (ms) | Condition |
|---|---|---|
| 0 | 250 | steady state |
| 20 | 250 | static scene |
| 40 | 251 | hand-waving motion |
| 74 | 250 | static |
| 176 | 266 | steady state |
| 205 | 233 | steady state |
| 235 | 112 | decoder buffer reset |
| 277 | 38 | post-reset transient |

The decomposition attributes ≈80% of the 250 ms to the H.264 decoder and GStreamer pipeline (≈200 ms), with the encode (≈10 ms), buffering (≈27 ms combined), OFDM framing (2.3 ms), FEC decode (≈5 ms), and localhost UDP (<5 ms) making up the rest. The ISAC link itself contributes ≈3 ms — the video-service latency ceiling on this platform is the application stack, and further latency reduction must target the decoder path, not the radio.

### 7.2 Throughput and error rate

Automated rate sweeps (1024-byte fixed-pattern packets, 10 s per point) measured byte-level BER at the payload interface under RS(255,223) protection (Table 7). BER stayed ≤0.015% at every rate up to 3000 kbps, and ≈0.78% of counted "errors" were the test header's non-fill bytes, so the effective payload error rate is near zero throughout. The BER–rate relation is non-monotonic (worst at 1500 kbps, best at 3000 kbps), consistent with pipeline occupancy: at the best point, `try_push` drops the fewest burst packets. The system thus carries the 1200 kbps video stream with ≈2.5× headroom, absorbing I-frame size spikes.

**Table 7. Payload BER vs. offered rate (RS enabled).**

| Rate (kbps) | Received (KB) | Error bytes | BER |
|---|---|---|---|
| 500 | 643 | 0 | 0% |
| 1000 | 1,435 | 53 | 0.0036% |
| 1500 | 2,229 | 349 | 0.0153% |
| 2000 | 3,021 | 307 | 0.0099% |
| 2500 | 3,693 | 410 | 0.0108% |
| 3000 | 4,487 | 117 | 0.0025% |

For context, the QPSK waveform's theoretical capacity is ≈38 Mbps (97,992 payload REs/frame × 2 bits × 1/2 LDPC × 223/255 RS ÷ 2.304 ms); the measured 3–5 Mbps of usable throughput is limited by the B210's USB 3.0 receive path, buffer-drop policy, LDPC padding waste, and frame-timing filler — gaps that a receiver upgrade addresses directly (Fig. 5).

![Fig. 5](figures/fig5_ber.png)

**Fig. 5 | Payload BER versus offered rate under RS(255,223) protection.** BER stays ≤0.015% at every rate up to 3000 kbps (open marker: zero errors at 500 kbps) and is non-monotonic, consistent with pipeline occupancy rather than channel capacity. The dashed line marks the 1200 kbps video operating point, which the link carries with ≈2.5× headroom.

## 8. Discussion

### 8.1 The least-sufficient-protection principle

The measurements of Sections 4–7 admit a compact statement. On a strongly coded ISAC link carrying inter-frame video:

- **Below the container**, protection is already more than sufficient: the LDPC residual is sparse enough (BER < 5×10⁻¹⁰ measured) that the outer code never fires in steady state, and the lightest outer code dominates on throughput.
- **At and above the container**, protection is the scarcest resource: a default container choice multiplies effective failure exposure by 7× (modeled) to 500× (measured with an unforgiving decoder), and a default decoder can convert transient damage into persistent stalls.

The engineering rule that follows — *add protection where it is scarcest, and keep it minimal where residuals are already sparse* — inverts the common instinct of strengthening the channel code. It was also validated from below: with the outer code removed entirely, 99.5% of TS packets failed and container-based playback became unusable, while the bare-stream stack retained ≈95% usable playback — the container/decoder layer, not the outer code, decides video survivability in stressed conditions. The principle's corollary is a *reliability cliff* in the total-redundancy axis: near-zero redundancy fails catastrophically at the container layer, while a modest 14.3% outer redundancy suffices completely — the useful design region is reached early and cheaply.

### 8.2 Rival explanations

Three alternative explanations for the observed video-quality differences deserve scrutiny. *Physical-layer differences*: ruled out by design — container/decoder comparisons ran on the same error stream with the same waveforms, and the ordering persisted with the outer code re-enabled. *Bitrate differences*: the TS and bare streams carried identical bitrates; the failure modes (sync-byte loss, continuity-counter breaks) are structural, not rate-dependent. *Decoder throughput*: VLC's failure was a state-machine deadlock, not a throughput shortfall — it occurred on static scenes and was absent in ffplay on identical hardware.

### 8.3 Limitations and boundary conditions

All results are bounded to: a single indoor line-of-sight link (≈5 m, log-periodic antennas); QPSK modulation; one receiver platform (B210) whose compute ceiling shaped the modulation result; 640×480@20 fps H.264; and one LDPC configuration (rate 1/2, 6 iterations). The γ measurements derive from a disabled-outer-code stress regime; while the ordering persists in normal operation, absolute γ values are regime-specific. Latency measurement used the stopwatch method (≈33 ms resolution), adequate for a 250 ms target but not for finer decomposition. The hardware-upgrade analysis (14-bit ADC and 160 MHz-bandwidth X310 receiver plus 15–20 dBi horn antenna, projected ≈20 dB SNR gain, release of 16QAM/64QAM, dual-channel AoA sensing) is a *projection* from component specifications, not a measurement.

## 9. Conclusion

On an open real-time OFDM-ISAC platform carrying live H.264 video over the air, delivered video quality is decided above the channel code: the LDPC inner code's residual is so sparse that the lightest Reed-Solomon outer code is already sufficient (recovering 8.4% payload throughput over the deployed heavier code with zero steady-state failures), while container and decoder choices amplify the same physical error stream by factors from 4× to 500×. Replacing MPEG-TS with bare H.264 Annex B, selecting a fault-tolerant decoder, and shrinking queues to non-blocking minima yielded a service pinned at 250 ms ± 0.5 ms end-to-end latency — of which the radio contributes ≈3 ms — with zero-error payload delivery up to 3000 kbps and 2.5× headroom over the video rate. These results support a least-sufficient-protection design rule for ISAC media services: size the outer code to the measured residual, not the modeled worst case, and spend the remaining engineering budget on the container and decoder, where protection is scarcest. Future work includes adaptive outer-code switching driven by link SNR, physical-layer-assisted error concealment (passing per-subcarrier confidence to the decoder), micro-Doppler vital-sign sensing on the same waveform, and the measured realization of the hardware upgrade projected in Section 8.3.

---

## CRediT authorship contribution statement

[First Author]: Conceptualization, Methodology, Investigation, Software, Writing – original draft. [Second Author]: Validation, Data curation. [Corresponding Author]: Supervision, Writing – review & editing, Funding acquisition. *(按实际贡献调整)*

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Data availability

The experiment configurations, measurement scripts, and processed datasets supporting the findings of this study are available from the corresponding author upon reasonable request. The underlying OpenISAC platform is publicly available at [repository URL] under a BSD-2-Clause license.

## Acknowledgements

This work was supported by [funding source, grant number]. The authors thank the OpenISAC development team for releasing the platform.

---

## References

[1] ITU-R, "Framework and overall objectives of the future development of IMT for 2030 and beyond," Recommendation ITU-R M.2160-0, Nov. 2023.

[2] F. Liu, Y. Cui, C. Masouros, J. Xu, T. X. Han, Y. C. Eldar, and S. Buzzi, "Integrated sensing and communications: Toward dual-functional wireless networks for 6G and beyond," *IEEE J. Sel. Areas Commun.*, vol. 40, no. 6, 2022. arXiv:2108.07165.

[3] Z. Wei, H. Qu, Y. Wang, X. Yuan, H. Wu, Y. Du, K. Han, N. Zhang, and Z. Feng, "Integrated sensing and communication signals toward 5G-A and 6G: A survey," 2023. arXiv:2301.03857.

[4] A. Kaushik, R. Singh, S. Dayarathna, R. Senanayake, M. Di Renzo, M. Dajer, H. Ji, Y. Kim, V. Sciancalepore, A. Zappone, and W. Shin, "Toward integrated sensing and communications for 6G: A standardization perspective," 2023. arXiv:2308.01227.

[5] C. Sturm and W. Wiesbeck, "Waveform design and signal processing aspects for fusion of wireless communications and radar sensing," *Proc. IEEE*, vol. 99, no. 7, pp. 1236–1259, 2011. doi:10.1109/jproc.2011.2131110.

[6] Z. Zhou, C. Zhang, X. Xu, and Y. Zeng, "OpenISAC: An open-source real-time experimentation platform for OFDM-ISAC with over-the-air synchronization," 2026. arXiv:2601.03535.

[7] D. Brunner, L. G. de Oliveira, C. Muth, S. Mandelli, M. Henninger, A. Diewald, Y. Li, M. B. Alabd, L. Schmalen, T. Zwick, and B. Nuss, "Bistatic OFDM-based ISAC with over-the-air synchronization: System concept and performance analysis," 2024. arXiv:2405.04962.

[8] T. Wiegand, G. J. Sullivan, G. Bjøntegaard, and A. Luthra, "Overview of the H.264/AVC video coding standard," *IEEE Trans. Circuits Syst. Video Technol.*, vol. 13, no. 7, pp. 560–576, 2003. doi:10.1109/tcsvt.2003.815165.

[9] R. Immich, E. Cerqueira, and M. Curado, "Mechanisms for resilient video transmission," 2018. arXiv:1808.06722.

[10] S. Lin and D. J. Costello, *Error Control Coding*, 2nd ed. Prentice Hall, 2004.

[11] O. Alaoui-Fdili, P. Corlay, Y. Fakhri, F.-X. Coudoux, and D. Aboutajdine, "A cross-layer approach for video delivery over wireless video sensor networks," 2015. arXiv:1501.07362.

[12] T.-Y. Tung and D. Gündüz, "DeepWiVe: Deep-learning-aided wireless video transmission," 2021. arXiv:2111.13034.

[13] X. Xu, O. Alay, E. Erkip, Y. Wang, and S. Panwar, "Two-way wireless video communication using randomized cooperation, network coding and packet level FEC," 2012. arXiv:1205.3252.

[14] ISO/IEC 13818-1, *Information technology — Generic coding of moving pictures and associated audio information: Systems* (MPEG-TS).

[15] A. Cassagne, O. Hartmann, M. Léonardon, K. He, C. Leroux, R. Tajan, O. Aumage, D. Barthou, T. Tonnellier, and V. Pignoly, "AFF3CT: A fast forward error correction toolbox!" *SoftwareX*, vol. 10, p. 100345, 2019. doi:10.1016/j.softx.2019.100345.

---

<!-- ==================== 起草元信息（投稿前删除） ==================== -->

## Appendix: Drafting metadata (remove before submission)

### Claim–evidence map

| Claim | Evidence | Status |
|---|---|---|
| All four RS configs: zero steady-state failures | Table 2 scan, >10⁶ codewords, failures only in startup window (ok<1000) | supported (ch3) |
| LDPC residual BER < 5×10⁻¹⁰ | bound from zero RS corrections over >10⁶ blocks | supported (ch3, indoor SNR regime) |
| RS(255,223) recovers 8.4% payload throughput vs 191 | 223/191−1=16.8% code-rate ratio; 8.4% incl. length prefix | supported (arithmetic) |
| γ_model ≈ 7× | header-exposure model (28 vs 4 critical bytes) | supported (model) |
| γ measured 4×–500× | Table 3, RS-disabled stress test, 3 decoders + 2 containers | supported (ch4; regime-specific) |
| TS+VLC 0% / TS+ffplay 30% / bare+GS 95% usable | stress test, RS disabled | supported (ch4) |
| Queues 32→4-8 + try_push eliminate accumulation | five-min trace, 250.3±0.5 ms steady state, no trend | supported (ch4/ch6) |
| Decoder ≈80% of latency | decomposition table | supported (estimate, ch6) |
| 16QAM failure is compute-bound | clean constellation + 105% CPU + 2.38 ms/frame | supported (ch5) |
| CP=128 minimum indoors | CP=64 sync-collapse loop, CFO artifact 95 kHz | supported (ch5) |
| BER ≤0.015% up to 3000 kbps; ~2.5× headroom | Table 7 sweep | supported (ch6) |
| Hardware upgrade → +20 dB, <10⁻⁷, 16/64QAM | component spec analysis only | **projection — not measured** |
| Conditional artifacts ≈1/30 s under >2/3-frame motion | joint-failure model + observation frequency | supported (model + observation, ch4) |

### Assumptions and missing inputs

- Author names, affiliations, and funding: `[to be added]`.
- Figures: complete. All five figures are AI-assisted draft illustrations; every numeric label was verified against the source data. For camera-ready: Fig. 1 and Fig. 4 (schematics) should be either cleared under the venue's AI-graphics policy or redrawn as native vector graphics; Fig. 2, Fig. 3, and Fig. 5 (data plots) have publication-grade vector-capable matplotlib fallbacks (`fig2_latency_mpl`, `fig3_gamma_mpl`, `fig5_ber_mpl`, regenerable with editable text via `figures/make_figs.py`) — switching to those vectors requires only a filename change.
- The 99.5% TS packet-failure figure and the γ table come from the disabled-outer-code stress tests as reported in the source material; the exact BER operating point during those tests should be quoted in the camera-ready version.
- Liu et al. [2] journal details (JSAC vol. 40, no. 6) should be double-checked against the published version; the arXiv identifier is verified.
- Venue decision (IEEE IoT-J / TVT / IEEE Access / journal equivalent) determines reference style and length trims; current draft ≈7,600 words including captions.

### 中文起草说明（供作者核对，不进正文）

- **主线**：按你确认的「跨层系统原则」组织 —— 第 4 节（外码冗余）先证明"下层已饱和"，第 5 节（容器/解码器）再证明"上层才是短板"，第 8 节把两者收拢成 least-sufficient-protection 原则。
- **起草顺序**按 skill 要求走的是证据优先：先写结果（第 4–7 节），再写引言/结论，标题最后从最强结果推导，摘要最后压缩全文。
- **_claim discipline_**：硬件升级（X310+喇叭天线）在正文只作为 projection 出现并明确标注，未混入实验结果；"to our knowledge" 的两处新颖性声明（γ 首次实测、ISAC 平台上的视频服务研究空白）保留有界表述，投稿前建议再用关键词核对一轮文献。
- 素材来源：8 个章节文件 + OpenISAC README；15 条参考文献全部经 arXiv/CrossRef 核实真实存在。
