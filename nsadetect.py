import subprocess
import re
import time
import threading
import os
import shutil
import logging

# Setup logging for verbose output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to trigger /usr/bin/sample on a specific process (launchd in this case)
def trigger_sample():
    try:
        logging.info("Triggering sample on launchd (pid 1) for 5 seconds...")
        subprocess.run(["sudo", "/usr/bin/sample", "1", "5"], check=True)
        logging.info("Sample completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running sample: {e}")
        return False
    return True

# Function to check if libdz.dylib is loaded in any running process using lsof
def check_libdz_lsof():
    try:
        logging.info("Checking for libdz.dylib using lsof...")
        while True:  # Continuous checking while sampling
            lsof_output = subprocess.check_output(["lsof"], text=True)

            # Search for libdz.dylib in the lsof output
            if re.search(r'libdz\.dylib', lsof_output):
                logging.info("libdz.dylib detected in the system!")
                return True
            else:
                logging.info("libdz.dylib not found in any running process. Retrying...")
            
            time.sleep(2)  # Wait for 2 seconds before retrying
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running lsof: {e}")
        return False

# Function to check for libdz.dylib using fs_usage (file system usage monitor)
def check_libdz_fs_usage():
    try:
        logging.info("Checking for libdz.dylib using fs_usage...")
        fs_usage_output = subprocess.check_output(["sudo", "fs_usage"], text=True, timeout=5)

        # Search for libdz.dylib in the fs_usage output
        if re.search(r'libdz\.dylib', fs_usage_output):
            logging.info("libdz.dylib detected in the file system usage!")
            return True
        else:
            logging.info("libdz.dylib not found in fs_usage output.")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running fs_usage: {e}")
        return False

# Function to monitor process activity using dtrace
def check_libdz_dtrace():
    try:
        logging.info("Monitoring process activity using dtrace...")
        dtrace_output = subprocess.check_output(["sudo", "dtrace", "-n", "syscall::open:entry"], text=True, timeout=5)

        # Search for libdz.dylib in the dtrace output
        if re.search(r'libdz\.dylib', dtrace_output):
            logging.info("libdz.dylib detected in dtrace syscall monitoring!")
            return True
        else:
            logging.info("libdz.dylib not detected in dtrace syscall activity.")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running dtrace: {e}")
        return False

# Function to check process information using Activity Monitor
def check_libdz_activity_monitor():
    try:
        logging.info("Checking Activity Monitor for libdz.dylib...")
        activity_monitor_output = subprocess.check_output(["ps", "aux"], text=True)

        # Search for libdz.dylib in process activity
        if re.search(r'libdz\.dylib', activity_monitor_output):
            logging.info("libdz.dylib detected in Activity Monitor!")
            return True
        else:
            logging.info("libdz.dylib not found in Activity Monitor process list.")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error checking Activity Monitor: {e}")
        return False

# Function to search for libdz.dylib in the file system
def search_libdz():
    logging.info("Searching the file system for libdz.dylib...")
    try:
        find_output = subprocess.check_output(["sudo", "find", "/", "-name", "libdz.dylib"], text=True)
        if find_output:
            logging.info(f"libdz.dylib found at the following locations:\n{find_output}")
            return find_output.strip().split("\n")
        else:
            logging.info("libdz.dylib not found in the file system.")
            return []
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running find: {e}")
        return []

# Function to copy libdz.dylib to the current directory
def copy_libdz_to_current_dir(file_path):
    try:
        current_dir = os.getcwd()
        destination_path = os.path.join(current_dir, "libdz.dylib")
        shutil.copy(file_path, destination_path)
        logging.info(f"Copied libdz.dylib to {destination_path}")
    except Exception as e:
        logging.error(f"Error copying libdz.dylib: {e}")

# Function to analyze libdz.dylib using codesign
def analyze_libdz_with_codesign(file_path):
    try:
        logging.info(f"Analyzing {file_path} with codesign...")
        codesign_output = subprocess.check_output(["codesign", "-dv", "--verbose=4", file_path], text=True)
        logging.info(f"Codesign output for {file_path}:\n{codesign_output}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running codesign on {file_path}: {e}")

# Function to analyze libdz.dylib using otool
def analyze_libdz_with_otool(file_path):
    try:
        logging.info(f"Analyzing {file_path} with otool...")
        otool_output = subprocess.check_output(["otool", "-L", file_path], text=True)
        logging.info(f"otool output for {file_path}:\n{otool_output}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running otool on {file_path}: {e}")

# Function to handle all actions after detection
def post_detection_analysis(file_path):
    # Analyze libdz.dylib using codesign and otool
    analyze_libdz_with_codesign(file_path)
    analyze_libdz_with_otool(file_path)

    # Copy libdz.dylib to the current working directory
    copy_libdz_to_current_dir(file_path)

if __name__ == "__main__":
    # Create threads for sampling, detection using lsof, fs_usage, dtrace, and Activity Monitor
    sample_thread = threading.Thread(target=trigger_sample)
    lsof_thread = threading.Thread(target=check_libdz_lsof)
    fs_usage_thread = threading.Thread(target=check_libdz_fs_usage)
    dtrace_thread = threading.Thread(target=check_libdz_dtrace)
    activity_monitor_thread = threading.Thread(target=check_libdz_activity_monitor)

    # Start all threads
    sample_thread.start()
    lsof_thread.start()
    fs_usage_thread.start()
    dtrace_thread.start()
    activity_monitor_thread.start()

    # Wait for the sample thread to finish before proceeding to further analysis
    sample_thread.join()

    # Wait for all detection threads to complete
    lsof_thread.join()
    fs_usage_thread.join()
    dtrace_thread.join()
    activity_monitor_thread.join()

    # Search for libdz.dylib on the filesystem
    file_paths = search_libdz()

    # If found, perform post-detection analysis and exit the loop
    if file_paths:
        for file_path in file_paths:
            post_detection_analysis(file_path)
    else:
        logging.info("libdz.dylib not found yet. Restarting detection.")

        # If libdz.dylib is not found, restart the detection process
        sample_thread = threading.Thread(target=trigger_sample)
        lsof_thread = threading.Thread(target=check_libdz_lsof)
        fs_usage_thread = threading.Thread(target=check_libdz_fs_usage)
        dtrace_thread = threading.Thread(target=check_libdz_dtrace)
        activity_monitor_thread = threading.Thread(target=check_libdz_activity_monitor)

        # Start threads again
        sample_thread.start()
        lsof_thread.start()
        fs_usage_thread.start()
        dtrace_thread.start()
        activity_monitor_thread.start()
        
        # Loop this process until detection
        sample_thread.join()
        lsof_thread.join()
        fs_usage_thread.join()
        dtrace_thread.join()
        activity_monitor_thread.join()

        # Sleep before restarting the detection loop
        time.sleep(5)

