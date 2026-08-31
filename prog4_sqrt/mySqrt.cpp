#include <immintrin.h>
#include <cmath>

void sqrtAVX2(int N,
              float initialGuess,
              float values[],
              float output[])
{
    const __m256 vThreshold = _mm256_set1_ps(0.00001f);
    const __m256 vOne       = _mm256_set1_ps(1.0f);
    const __m256 vThree     = _mm256_set1_ps(3.0f);
    const __m256 vHalf      = _mm256_set1_ps(0.5f);
    // fabs: ~(-0.0f) & val
    const __m256 vAbsMask   = _mm256_set1_ps(-0.0f);

    int i = 0;
    // 主循环：每次并行处理 8 个 float
    for (; i <= N - 8; i += 8) {
        __m256 vx = _mm256_loadu_ps(&values[i]);
        __m256 vguess = _mm256_set1_ps(initialGuess);

        // 计算初始 error = fabs(guess * guess * x - 1.f)
        __m256 vguess2  = _mm256_mul_ps(vguess, vguess);
        __m256 vterm    = _mm256_mul_ps(vguess2, vx);
        __m256 verr_raw = _mm256_sub_ps(vterm, vOne);
        __m256 verror   = _mm256_andnot_ps(vAbsMask, verr_raw); // 清除符号位

        // 比较：error > kThreshold
        __m256 vmask = _mm256_cmp_ps(verror, vThreshold, _CMP_GT_OQ);
        int mask = _mm256_movemask_ps(vmask);

        // 只要 8 个通道中还有任意一个未收敛 (mask != 0)，就继续迭代
        while (mask != 0) {
            // 代数化简: (3.f * guess - x * guess^3) * 0.5f = 0.5f * guess * (3.0f - x * guess^2)
            vguess2 = _mm256_mul_ps(vguess, vguess);
            __m256 vsub = _mm256_sub_ps(vThree, _mm256_mul_ps(vx, vguess2));
            __m256 vmul = _mm256_mul_ps(vguess, vsub);
            vguess      = _mm256_mul_ps(vHalf, vmul);

            // 更新 error 状态
            vguess2  = _mm256_mul_ps(vguess, vguess);
            verr_raw = _mm256_sub_ps(_mm256_mul_ps(vguess2, vx), vOne);
            verror   = _mm256_andnot_ps(vAbsMask, verr_raw);

            vmask = _mm256_cmp_ps(verror, vThreshold, _CMP_GT_OQ);
            mask  = _mm256_movemask_ps(vmask);
        }

        // output[i] = x * guess
        __m256 vres = _mm256_mul_ps(vx, vguess);
        _mm256_storeu_ps(&output[i], vres);
    }

    // 尾部边界处理
    static const float kThreshold = 0.00001f;
    for (; i < N; i++) {
        float x = values[i];
        float guess = initialGuess;
        float error = fabs(guess * guess * x - 1.f);
        while (error > kThreshold) {
            guess = (3.f * guess - x * guess * guess * guess) * 0.5f;
            error = fabs(guess * guess * x - 1.f);
        }
        output[i] = x * guess;
    }
}
