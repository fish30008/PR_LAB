# test_concurrent_clients.py
import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import logging

URL_LIST = [
    'http://server:1337/content/',
    'http://server:1337/content/map/',
    'http://server:1337/content/map/TEXT.txt',
    'http://server:1337/content/map/PNG.png'
]
# NUM_CLIENTS = 10
#
# def make_request(i):
#     start = time.time()
#     URL = random.choice(URL_LIST)
#     r = requests.get(URL)
#     elapsed = time.time() - start
#     print(f"Client {i}: {r.status_code} in {elapsed:.2f}s")
#     return elapsed
#
# def main():
#     start = time.time()
#     with ThreadPoolExecutor(max_workers=NUM_CLIENTS) as executor:
#         results = list(executor.map(make_request, range(NUM_CLIENTS)))
#     total = time.time() - start
#
#     print("\n--- Results ---")
#     print(f"Total time: {total:.2f} seconds")
#     print(f"Average per request: {sum(results)/NUM_CLIENTS:.2f} seconds")

# if __name__ == "__main__":
#     main()

MODE = sys.argv[1] if len(sys.argv) > 1 else "gentle"

print(f'Mode is = {MODE}')


def make_request(i):
    start = time.time()
    URL = random.choice(URL_LIST)
    try:
        r = requests.get(URL)
        elapsed = time.time() - start
        print(f"{MODE.capitalize()} Client {i}: {r.status_code} in {elapsed:.2f}s")
    except Exception as e:
        print(f"{MODE.capitalize()} Client {i} error: {e}")

def run_client(rate_per_sec):
    threads = []
    for i in range(30):  # total requests
        t = threading.Thread(target=make_request, args=(i,))
        t.start()
        threads.append(t)
        time.sleep(1 / rate_per_sec)
    for t in threads:
        t.join()

if MODE == "spam":
    run_client(rate_per_sec=10)
else:
    run_client(rate_per_sec=1)


