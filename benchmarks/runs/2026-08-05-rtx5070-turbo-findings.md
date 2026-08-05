**Findings (q1729)**  

**Classical CUDA kernel (Ramanujan‑1914 series)**  
- With a single term (`n_terms = 1`) the kernel returns π ≈ 3.1415927300133055, giving an absolute error of **7.642 × 10⁻⁸** (≈ 7.6 correct digits) and a mean wall‑time of **0.00267 s** (min 0.00236 s).  
- Adding a second term (`n_terms = 2`) drives the error down to **4.44 × 10⁻¹⁶** (≈ 15.85 correct digits) while the mean runtime rises only slightly to **0.00271 s** (min 0.00246 s).  
- From `n_terms = 3` onward the reported absolute error is **0.0** and the correct‑digit count saturates at **16.0** (the limits of IEEE‑754 double precision). Mean runtimes remain low‑millisecond, growing slowly with term count:  
  - `n_terms = 4 096` → mean **0.01368 s** (min 0.00490 s)  
  - `n_terms = 16 384` → mean **0.068997 s** (min 0.068610 s)  
- GPU utilization stays low for small workloads (peak ≈ 6 % at `n_terms = 1`) but rises with workload, reaching a peak of **95 %** GPU utilization at `n_terms = 16 384` (power draw ≈ 37.7 W).  

**Quantum Amplitude Estimation (QAE) simulated on cuStateVec**  
- With 2 counting qubits (`m = 2`) the algorithm yields π ≈ 2.0000, error **1.1416**, correct digits **0.44**, mean runtime **0.3415 s** (min 0.3179 s).  
- Increasing to `m = 3` reduces the error to **0.2726** (≈ 1.06 correct digits) with a similar mean time **0.3455 s**.  
- At `m = 5` the error drops to **0.03045** (≈ 2.01 correct digits) and the mean time is **0.3552 s**.  
- By `m = 8` the error reaches **0.01002** (≈ 2.50 correct digits) and the mean time is **0.3753 s**.  
- The error plateaus at **≈ 3.116 × 10⁻⁵** (≈ 5.00 correct digits) for `m ≥ 10` (see rows for `m = 10, 14, 15, 16`).  
- Runtime grows roughly exponentially with the number of counting qubits:  
  - `m = 14` → mean **2.3409 s** (min 2.2317 s)  
  - `m = 15` → mean **4.5703 s** (min 4.4457 s)  
  - `m = 16` → mean **9.2905 s** (min 9.0019 s)  
- GPU utilization remains low throughout the quantum runs (peak ≤ 20 % at `m = 16`), indicating that wall‑time is dominated by kernel‑launch and dispatch overhead rather than raw state‑vector arithmetic.  

**Anomalies & Observations**  
- The classical kernel’s error drops to zero from `n_terms = 3` onward, reflecting saturation of IEEE‑754 double‑precision arithmetic rather than continued series convergence.  
- The QAE error stops improving after `m = 10`; the phase error (≈ 3.0 × 10⁻⁶) is already smaller than the phase resolution (≈ 6.1 × 10⁻⁵) at that point, so further increases in `m` only raise cost without improving accuracy—a point noted in the study’s limitations.  
- Only one GPU configuration is present (RTX 5070 Laptop GPU, 8151 MiB VRAM, turbo power profile), so no cross‑hardware comparison can be made from this dataset.  

**Overall Gap**  
- To reach double‑precision precision (~1e‑16 error) the classical kernel needs only two terms and completes in **≈ 2.7 ms**.  
- Achieving comparable error with the simulated QAE would require an error far below the plateau (~3e‑05), which is unattainable with the given circuit; the best achievable error (~3e‑05) corresponds to about **5 correct digits** and costs **≥ 2.3 s** (for `m = 14`), i.e., roughly three orders of magnitude slower than the classical approach for a far worse precision.  

These observations confirm the hypothesis that, on this RTX 5070 laptop GPU, the hand‑written CUDA Ramanujan kernel reaches machine‑precision accuracy in sub‑millisecond time, while the simulated QAE remains limited by algorithmic plateau and simulation overhead, showing no crossover within the tested parameter range.