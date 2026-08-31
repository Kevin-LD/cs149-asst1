import subprocess
import re
import matplotlib.pyplot as plt

# 可执行文件路径与测试线程范围
EXECUTABLE = "./mandelbrot"
THREAD_COUNTS = list(range(1, 9))  # 1 到 8 线程
VIEW_OPTION = ["-v", "2"]  # 如果想测试 view 2，可以设置为 ["-v", "2"]

threads = []
serial_times = []
parallel_times = []
speedups = []

print(f"{'Threads':<10}{'Serial (ms)':<15}{'Parallel (ms)':<15}{'Speedup':<10}")
print("-" * 50)

for t in THREAD_COUNTS:
    cmd = [EXECUTABLE, "-t", str(t)]
    if VIEW_OPTION:
        cmd.extend(VIEW_OPTION)

    # 执行程序并捕获输出
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    # 正则提取时间数据
    serial_match = re.search(r'\[mandelbrot serial\]:\s*\[([\d\.]+)\]\s*ms', output)
    thread_match = re.search(r'\[mandelbrot thread\]:\s*\[([\d\.]+)\]\s*ms', output)

    if serial_match and thread_match:
        t_serial = float(serial_match.group(1))
        t_parallel = float(thread_match.group(1))
        speedup = t_serial / t_parallel

        threads.append(t)
        serial_times.append(t_serial)
        parallel_times.append(t_parallel)
        speedups.append(speedup)

        print(f"{t:<10}{t_serial:<15.3f}{t_parallel:<15.3f}{speedup:<10.2f}x")
    else:
        print(f"[Warning] Failed to parse output for -t {t}")

# 画图
plt.figure(figsize=(8, 5))
plt.plot(threads, speedups, marker='o', color='tab:blue', linewidth=2, label='Measured Speedup')
plt.plot(threads, threads, 'r--', alpha=0.7, label='Ideal Linear Speedup')

plt.title('Mandelbrot Thread Speedup', fontsize=14, fontweight='bold')
plt.xlabel('Number of Threads', fontsize=12)
plt.ylabel('Speedup (x)', fontsize=12)
plt.xticks(threads)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(fontsize=11)
plt.tight_layout()

output_png = f"plot/speedup_plot-v{VIEW_OPTION[1] if VIEW_OPTION else 'default'}.png"
plt.savefig(output_png, dpi=300)
print(f"\n[Success] Data saved and plot generated: {output_png}")
