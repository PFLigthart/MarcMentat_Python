import time
import re
import os.path


def does_status_file_exist(file_name, max_time):
    """
    Check if the status file exits. Runs untill found or max time reached

    Args:
        max_time: the maximum ammount of time the model can run.
    """

    file_exists = False
    elapsed_time = 0
    start_time = time.time()

    print("Checking")

    while (file_exists == False) and (elapsed_time < max_time):
        if os.path.isfile(f"{file_name}_job1.sts"):
            print("File exist")
            file_exists = True
        else:
            # pause for a short ammount of time
            time.sleep(0.1)
            elapsed_time = time.time() - start_time

    return


def was_code_successfull(file_path, word, max_time=15):
    """Search status file to see if code ran successfully"""
    complete = False
    time_elapsed = 0
    start_time = time.time()

    while (complete == False) and (time_elapsed < max_time):
        with open(file_path, "r") as file:
            # read all content of a file
            content = file.read()
            # check if string present in a file
            if word in content:
                print("Found Exit Code 3004")
                complete = True
            else:
                # pause for a short while
                time.sleep(0.1)
                time_elapsed = time.time() - start_time
