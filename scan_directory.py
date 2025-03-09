import os
import sys


def scan_directory(directory):
    file_info = []
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                file_info.append({"filename": filename, "size": file_size})
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return

    file_info.sort(key=lambda x: x["size"])

    print("Filename\t\tSize (bytes)")
    print("--------\t\t------------")
    for file in file_info:
        print(f"{file['filename']}\t\t{file['size']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scan_directory.py <directory_path>")
    else:
        directory_path = sys.argv[1]
        scan_directory(directory_path)
