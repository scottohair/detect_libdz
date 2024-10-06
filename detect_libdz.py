import subprocess
import re
import time
import threading
import os
import shutil
import logging
import sys
import platform
from typing import List

# Check if the script is running on macOS
if platform.system() != 'Darwin':
    print("This script is intended for macOS systems.")
    sys.exit(1)

# Check if the script is run with root permissions
if os.geteuid() != 0:
    print("This script must be run as root.")
    sys.exit(1)

# Setup logging with different levels
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Shared event to signal detection across threads
stop_event = threading.Event()

def trigger_sample():
    """
    Samples the 'launchd' process (PID 1) for 5 seconds.
    """
    try:
        logging.info("Triggering sample on launchd (pid 1) for 5 seconds...")
        subprocess.run(["/usr/bin/sample", "1", "5"], check=True)
        logging.info("Sample completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running sample: {e}")
    except Exception as e:
        logging.exception("An unexpected error occurred in trigger_sample.")

def check_libdz_lsof():
    """
    Checks for 'libdz.dylib' in open files using 'lsof'.
    """
    try:
        logging.info("Checking for libdz.dylib using lsof...")
        while not stop_event.is_set():
            lsof_output = subprocess.check_output(["lsof", "-n", "-P"], text=True, stderr=subprocess.DEVNULL)
            if re.search(r'libdz\.dylib', lsof_output):
                logging.info("libdz.dylib detected in the system via lsof!")
                stop_event.set()
                return
            time.sleep(2)
    except Exception as e:
        logging.exception("An unexpected error occurred in check_libdz_lsof.")

def check_libdz_fs_usage():
    """
    Monitors file system usage to detect 'libdz.dylib' access using 'fs_usage'.
    """
    try:
        logging.info("Checking for libdz.dylib using fs_usage...")
        fs_usage_process = subprocess.Popen(
            ["fs_usage"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )

        start_time = time.time()
        while not stop_event.is_set():
            line = fs_usage_process.stdout.readline()
            if 'libdz.dylib' in line:
                logging.info("libdz.dylib detected in file system usage via fs_usage!")
                stop_event.set()
                break
            if time.time() - start_time > 10:  # Monitor for 10 seconds
                break
        fs_usage_process.terminate()
    except Exception as e:
        logging.exception("An unexpected error occurred in check_libdz_fs_usage.")

def check_libdz_dtrace():
    """
    Monitors system calls related to file opening to detect 'libdz.dylib' using 'dtrace'.
    """
    try:
        logging.info("Monitoring process activity using dtrace...")
        dtrace_script = 'syscall::open*:entry { printf("%s\\n", copyinstr(arg0)); }'
        dtrace_process = subprocess.Popen(
            ["dtrace", "-n", dtrace_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )

        start_time = time.time()
        while not stop_event.is_set():
            line = dtrace_process.stdout.readline()
            if 'libdz.dylib' in line:
                logging.info("libdz.dylib detected in dtrace syscall monitoring!")
                stop_event.set()
                break
            if time.time() - start_time > 10:  # Monitor for 10 seconds
                break
        dtrace_process.terminate()
    except Exception as e:
        logging.exception("An unexpected error occurred in check_libdz_dtrace.")

def check_libdz_activity_monitor():
    """
    Checks the process list for 'libdz.dylib' using 'ps aux'.
    """
    try:
        logging.info("Checking Activity Monitor for libdz.dylib...")
        while not stop_event.is_set():
            activity_monitor_output = subprocess.check_output(["ps", "aux"], text=True)
            if re.search(r'libdz\.dylib', activity_monitor_output):
                logging.info("libdz.dylib detected in Activity Monitor process list!")
                stop_event.set()
                return
            time.sleep(2)
    except Exception as e:
        logging.exception("An unexpected error occurred in check_libdz_activity_monitor.")

def search_libdz() -> List[str]:
    """
    Searches the file system for both visible and hidden 'libdz.dylib' files.
    Returns a list of file paths where the library is found.
    """
    logging.info("Searching the file system for libdz.dylib (including hidden files)...")
    try:
        # Use find to locate both normal and hidden versions of libdz.dylib
        find_command = ["sudo", "find", "/", "-name", "libdz.dylib", "-o", "-name", ".libdz.dylib"]
        
        # Setting a timeout to prevent long-running searches
        find_output = subprocess.check_output(find_command, text=True, stderr=subprocess.DEVNULL, timeout=60)
        
        if find_output:
            file_paths = find_output.strip().split("\n")
            logging.info(f"libdz.dylib found at the following locations (including hidden files):\n{find_output}")
            return file_paths
        else:
            logging.info("libdz.dylib (including hidden files) not found in the file system.")
            return []
    
    except subprocess.TimeoutExpired:
        logging.error("The search for libdz.dylib timed out.")
        return []
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running find command: {e}")
        return []
    
    except Exception as e:
        logging.exception("An unexpected error occurred during the search for libdz.dylib.")
        return []

def copy_libdz_to_current_dir(file_path: str):
    """
    Copies 'libdz.dylib' from the specified file path to the current working directory.
    """
    try:
        current_dir = os.getcwd()
        destination_path = os.path.join(current_dir, "libdz.dylib")
        shutil.copy(file_path, destination_path)
        logging.info(f"Copied libdz.dylib to {destination_path}")
    except Exception as e:
        logging.exception(f"Error copying libdz.dylib from {file_path}.")

def analyze_libdz_with_codesign(file_path: str):
    """
    Analyzes 'libdz.dylib' using 'codesign' to check its code signature.
    """
    try:
        logging.info(f"Analyzing {file_path} with codesign...")
        codesign_output = subprocess.check_output(["codesign", "-dv", "--verbose=4", file_path], text=True, stderr=subprocess.STDOUT)
        logging.info(f"Codesign output for {file_path}:\n{codesign_output}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Codesign reported an error for {file_path}:\n{e.output}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred in analyze_libdz_with_codesign for {file_path}.")

def analyze_libdz_with_otool(file_path: str):
    """
    Analyzes 'libdz.dylib' using 'otool' to inspect its dependencies.
    """
    try:
        logging.info(f"Analyzing {file_path} with otool...")
        otool_output = subprocess.check_output(["otool", "-L", file_path], text=True)
        logging.info(f"otool output for {file_path}:\n{otool_output}")
    except subprocess.CalledProcessError as e:
        logging.error(f"otool reported an error for {file_path}:\n{e.output}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred in analyze_libdz_with_otool for {file_path}.")

def post_detection_analysis(file_path: str):
    """
    Performs post-detection analysis by analyzing and copying 'libdz.dylib'.
    """
    analyze_libdz_with_codesign(file_path)
    analyze_libdz_with_otool(file_path)
    copy_libdz_to_current_dir(file_path)

def cleanup():
    """
    Cleans up any remaining processes or resources before exiting.
    """
    logging.info("Cleaning up resources.")
    stop_event.set()
    # Additional cleanup code can be added here if necessary.

if __name__ == "__main__":
    try:
        while not stop_event.is_set():
            # Start the sample thread
            sample_thread = threading.Thread(target=trigger_sample)

            # Start detection threads
            detection_threads = [
                threading.Thread(target=check_libdz_lsof),
                threading.Thread(target=check_libdz_fs_usage),
                threading.Thread(target=check_libdz_dtrace),
                threading.Thread(target=check_libdz_activity_monitor),
            ]

            # Start all threads
            sample_thread.start()
            for thread in detection_threads:
                thread.start()

            # Wait for threads to finish or stop_event to be set
            sample_thread.join()
            for thread in detection_threads:
                thread.join()

            # Check if libdz.dylib has been found
            if stop_event.is_set():
                # Search for libdz.dylib on the filesystem
                file_paths = search_libdz()
                if file_paths:
                    for file_path in file_paths:
                        post_detection_analysis(file_path)
                    break
                else:
                    logging.warning("libdz.dylib detection triggered but not found in the file system.")
                    # Reset the event to restart detection
                    stop_event.clear()
            else:
                logging.info("libdz.dylib not detected. Restarting detection.")
                time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
    finally:
        cleanup()

