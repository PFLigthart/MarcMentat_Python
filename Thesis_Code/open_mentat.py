import os
import time

from py_mentat import py_connect, py_disconnect, py_send

start_time = time.time()
print(f"Opening Marc {start_time}")
os.system("mentat initiate_separate_process.proc -bg")
end_time = time.time()
print(f"Marc Opened {end_time - start_time}")
time.sleep(10)
