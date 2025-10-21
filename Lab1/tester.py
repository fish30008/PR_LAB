import threading
import time

# Shared resource
counter = 0

# Naive version (with race condition)
def increment_naive():
    global counter
    for _ in range(10000):
        temp = counter      # Read
        time.sleep(0.000001)  # Force thread switch → exposes race
        counter = temp + 1  # Write

# Thread-safe version (using a lock)
lock = threading.Lock()

def increment_safe():
    global counter
    for _ in range(10000):
        with lock:
            temp = counter
            time.sleep(0.000001)  # Still there, but protected
            counter = temp + 1

# --- Demo ---
if __name__ == "__main__":
    # Test naive version
    counter = 0
    t1 = threading.Thread(target=increment_naive)
    t2 = threading.Thread(target=increment_naive)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print(f"Naive result (should be 200000): {counter}")

    # Test safe version
    counter = 0
    t1 = threading.Thread(target=increment_safe)
    t2 = threading.Thread(target=increment_safe)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print(f"Safe result (should be 200000): {counter}")