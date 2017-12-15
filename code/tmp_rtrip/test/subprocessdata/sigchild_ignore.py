import signal, subprocess, sys, time
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
subprocess.Popen([sys.executable, '-c', 'print("albatross")']).wait()
p = subprocess.Popen([sys.executable, '-c', 'print("albatross")'])
num_polls = 0
while p.poll() is None:
    time.sleep(0.01)
    num_polls += 1
    if num_polls > 3000:
        raise RuntimeError('poll should have returned 0 within 30 seconds')
