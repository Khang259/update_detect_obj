# import multiprocessing
# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
# import matplotlib.ticker as ticker
# import time
# import psutil
# import random
# from collections import deque

# # Task function that simulates CPU-bound work
# def compute(task_id, log_queue):
#     proc_name = multiprocessing.current_process().name
#     start_time = time.time()
#     result = sum(i*i for i in range(1000000 + random.randint(0, 100000)))
#     end_time = time.time()
#     log_queue.put((proc_name, task_id, start_time, end_time))

# # Function to run multiprocessing tasks
# def run_tasks(num_tasks, log_queue):
#     processes = []
#     for i in range(num_tasks):
#         p = multiprocessing.Process(target=compute, args=(i, log_queue), name=f"Process-{i}")
#         p.start()
#         processes.append(p)
#     for p in processes:
#         p.join()

# # Start a multiprocessing.Manager to collect logs
# manager = multiprocessing.Manager()
# log_queue = manager.Queue()

# # Start multiprocessing in a separate process (non-blocking for animation)
# mp_process = multiprocessing.Process(target=run_tasks, args=(4, log_queue))
# mp_process.start()

# # Data storage
# cpu_usage = deque(maxlen=100)
# time_stamps = deque(maxlen=100)
# gantt_data = []

# # Set up plot
# fig, (ax_cpu, ax_gantt) = plt.subplots(2, 1, figsize=(10, 6))
# plt.tight_layout(pad=3)

# # Animation function
# def update(frame):
#     # Update CPU usage
#     cpu = psutil.cpu_percent()
#     timestamp = time.time()
#     cpu_usage.append(cpu)
#     time_stamps.append(timestamp)

#     ax_cpu.clear()
#     ax_cpu.plot(list(time_stamps), list(cpu_usage), label="CPU %")
#     ax_cpu.set_ylim(0, 100)
#     ax_cpu.set_ylabel("CPU Usage (%)")
#     ax_cpu.set_title("Live CPU Usage")
#     ax_cpu.legend()

#     # Collect logs from queue
#     while not log_queue.empty():
#         record = log_queue.get()
#         gantt_data.append(record)

#     # Update Gantt chart
#     ax_gantt.clear()
#     ax_gantt.set_title("Gantt Chart of Task Execution")
#     colors = {}

#     for idx, (proc, task_id, start, end) in enumerate(gantt_data):
#         if proc not in colors:
#             colors[proc] = (random.random(), random.random(), random.random())
#         ax_gantt.barh(proc, end - start, left=start, color=colors[proc])
    
#     ax_gantt.xaxis.set_major_locator(ticker.MaxNLocator(5))
#     ax_gantt.set_xlabel("Time (s)")

# ani = animation.FuncAnimation(fig, update, interval=500)
# plt.show()

# # Clean up
# mp_process.join()
