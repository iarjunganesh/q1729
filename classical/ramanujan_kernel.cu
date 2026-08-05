// Ramanujan's 1914 series for 1/pi — hand-written CUDA C++ baseline.
//
//     1/pi = (2*sqrt(2)/9801) * sum_{k>=0} (4k)! (1103 + 26390k) / ((k!)^4 396^(4k))
//
// One series term per thread, block-level shared-memory tree reduction, one
// partial sum written per block. The host sums the block partials (see
// classical/cuda_kernel.py) rather than the kernel using atomicAdd, so the
// result is bit-for-bit reproducible across runs — atomicAdd on doubles
// commits in nondeterministic order, and a benchmark whose output moves
// between identical runs cannot serve as evidence (docs/handbook/research-standards.md).
//
// Compiled at runtime by NVRTC via cupy.RawModule; see
// docs/adr/005-cuda-kernel-via-nvrtc.md for why there is no nvcc build step.
//
// Accuracy note: the term is built as a running product that interleaves the
// (4k)! numerator factors with the (k!)^4 and 396^(4k) denominators, so the
// accumulator never leaves double's exponent range. Computing (4k)! first
// would overflow around k = 43. Every factor below is exactly representable
// in double, so the per-term relative error stays at a few ULP — which is
// what makes the exact-SymPy comparison in classical/ramanujan_series.py a
// meaningful drift check rather than a formality.

extern "C" __global__ void ramanujan_terms(const int n_terms, double *block_sums)
{
    extern __shared__ double scratch[];

    const int tid = threadIdx.x;
    const int k = blockIdx.x * blockDim.x + tid;

    double term = 0.0;
    if (k < n_terms) {
        // 396^4, the per-iteration denominator contributed by 396^(4k).
        const double p396 = 396.0 * 396.0 * 396.0 * 396.0;

        term = 1103.0 + 26390.0 * (double)k;
        for (int i = 1; i <= k; ++i) {
            const double d = (double)i;
            // The four (4k)! factors this iteration brings in ...
            term *= (4.0 * d - 3.0) * (4.0 * d - 2.0) * (4.0 * d - 1.0) * (4.0 * d);
            // ... divided straight back down by (k!)^4 and 396^(4k).
            term /= d * d * d * d;
            term /= p396;
        }
    }

    scratch[tid] = term;
    __syncthreads();

    // Tree reduction over the block. blockDim.x is a power of two (enforced
    // host-side), so no odd-element special case is needed.
    for (unsigned int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (tid < stride) {
            scratch[tid] += scratch[tid + stride];
        }
        __syncthreads();
    }

    if (tid == 0) {
        block_sums[blockIdx.x] = scratch[0];
    }
}
