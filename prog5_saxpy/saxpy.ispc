
// export void saxpy_ispc(uniform int N,
//                        uniform float scale,
//                             uniform float X[],
//                             uniform float Y[],
//                             uniform float result[])
// {
//     foreach (i = 0 ... N) {           
//         result[i] = scale * X[i] + Y[i];
//     }
// }

// task void saxpy_ispc_task(uniform int N,
//                                uniform int span,
//                                uniform float scale,
//                                uniform float X[], 
//                                uniform float Y[],
//                                uniform float result[])
// {

//     uniform int indexStart = taskIndex * span;
//     uniform int indexEnd = min(N, indexStart + span);

//     foreach (i = indexStart ... indexEnd) {
//         result[i] = scale * X[i] + Y[i];
//     }
// }

// export void saxpy_ispc_withtasks(uniform int N,
//                                uniform float scale,
//                                uniform float X[],
//                                uniform float Y[],
//                                uniform float result[])
// {

//     uniform int span = N / 64;  // 64 tasks

//     launch[N/span] saxpy_ispc_task(N, span, scale, X, Y, result);
    
// }

// streaming store version
// streaming store 一次写入 32 字节，因此写入的地址必须是 32-Byte 对齐的。
// 在 main 中分配内存时也需要注意，必须分配 32-Byte 对齐的内存。否则会报错。
export void saxpy_ispc(uniform int N,
                       uniform float scale,
                       uniform float X[],
                       uniform float Y[],
                       uniform float result[])
{
    for (uniform int i = 0; i + programCount <= N; i += programCount) {
        varying int index = i + programIndex;

        varying float v = scale * X[index] + Y[index];

        streaming_store(result + i, v);
    }

    uniform int tail = (N / programCount) * programCount;

    for (uniform int i = tail; i < N; ++i) {
        result[i] = scale * X[i] + Y[i];
    }
}

task void saxpy_ispc_task(uniform int N,
                          uniform int span,
                          uniform float scale,
                          uniform float X[],
                          uniform float Y[],
                          uniform float result[])
{
    // span 必须是 8 的倍数（float 4 Byte * 8 = 32 Byte）
    uniform int indexStart = taskIndex * span;
    uniform int indexEnd = min(N, indexStart + span);

    uniform int i;

    // Main SIMD loop
    for (i = indexStart;
         i + programCount <= indexEnd;
         i += programCount) {

        varying int index = i + programIndex;

        varying float v = scale * X[index] + Y[index];

        streaming_store(result + i, v);
    }

    // Tail
    for (; i < indexEnd; ++i) {
        result[i] = scale * X[i] + Y[i];
    }
}

export void saxpy_ispc_withtasks(uniform int N,
                                 uniform float scale,
                                 uniform float X[],
                                 uniform float Y[],
                                 uniform float result[])
{
    // Make span a multiple of 8, for alignment
    // ceil(N/(64*8)) * 8
    uniform int span =
        ((N / 64 + 7) / 8) * 8;

    uniform int numTasks = (N + span - 1) / span;

    launch[numTasks] saxpy_ispc_task(
        N, span, scale, X, Y, result);
}
