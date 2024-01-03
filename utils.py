import os
import requests

def file_system_operations(job_id, _):
    print(f"{job_id}: Performing file system operations")
    os.makedirs("test_dir", exist_ok=True)
    with open("test_dir/test_file.txt", "w") as file:
        file.write("Hello, World!")
    os.remove("test_dir/test_file.txt")
    os.rmdir("test_dir") 

def file_operations(job_id, _):
    print(f"{job_id}: Performing file operations")
    with open("example.txt", "w") as file:
        file.write("Sample text")
    with open("example.txt", "r") as file:
        content = file.read()
    print(f"{job_id}: File content: {content}")
    os.remove("example.txt")

def network_operations(job_id, _):
    print(f"{job_id}: Performing network operations")
    url = "https://www.example.com"
    response = requests.get(url)
    print(f"{job_id}: Response status code: {response.status_code}")
