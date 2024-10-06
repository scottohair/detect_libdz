import subprocess
import re
import time
import os

# Function to trigger /usr/bin/sample on a specific process (launchd in this case)
def trigger_sample():
    try:
        print("Triggering sample on launchd (pid 1) for 5 seconds...")
        subprocess.run(["sudo", "/usr/bin/sample", "1", "5"], check=True)
        print("Sample completed.")
    except subprocess.CalledProcessError as e:
        print(f"Error running sample: {e}")
        return False
    return True

# Function to check if libdz.dylib is loaded in any running process
def check_libdz():
    try:
        print("Checking for libdz.dylib using lsof...")
        lsof_output = subprocess.check_output(["lsof"], text=True)
        
        # Search for libdz.dylib in the lsof output
        if re.search(r'libdz\.dylib', lsof_output):
            print("libdz.dylib detected in the system!")
            return True
        else:
            print("libdz.dylib not found in any running process.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error running lsof: {e}")
        return False

# Function to search for libdz.dylib in the file system
def search_libdz():
    print("Searching the file system for libdz.dylib...")
    try:
        find_output = subprocess.check_output(["sudo", "find", "/", "-name", "libdz.dylib"], text=True)
        if find_output:
            print(f"libdz.dylib found at the following locations:\n{find_output}")
            return find_output.strip().split("\n")
        else:
            print("libdz.dylib not found in the file system.")
            return []
    except subprocess.CalledProcessError as e:
        print(f"Error running find: {e}")
        return []

# Function to analyze libdz.dylib using codesign
def analyze_libdz_with_codesign(file_path):
    try:
        print(f"Analyzing {file_path} with codesign...")
        codesign_output = subprocess.check_output(["codesign", "-dv", "--verbose=4", file_path], text=True)
        print(f"Codesign output for {file_path}:\n{codesign_output}")
    except subprocess.CalledProcessError as e:
        print(f"Error running codesign on {file_path}: {e}")

# Function to analyze libdz.dylib using otool
def analyze_libdz_with_otool(file_path):
    try:
        print(f"Analyzing {file_path} with otool...")
        otool_output = subprocess.check_output(["otool", "-L", file_path], text=True)
        print(f"otool output for {file_path}:\n{otool_output}")
    except subprocess.CalledProcessError as e:
        print(f"Error running otool on {file_path}: {e}")

if __name__ == "__main__":
    # Step 1: Trigger /usr/bin/sample
    if trigger_sample():
        # Wait for 2 seconds after sampling
        time.sleep(2)
        
        # Step 2: Check if libdz.dylib is present in any running process
        if check_libdz():
            # Step 3: Search for libdz.dylib in the file system
            file_paths = search_libdz()

            # Step 4: If found, analyze libdz.dylib using codesign and otool
            for file_path in file_paths:
                analyze_libdz_with_codesign(file_path)
                analyze_libdz_with_otool(file_path)

