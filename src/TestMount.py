import os
import sys

# Adjust this to the path you mounted in your Container App
MOUNT_PATH = "/mnt/azurefileshare"

TEST_DIR = os.path.join(MOUNT_PATH, "test_dir")
TEST_FILE = os.path.join(TEST_DIR, "test_file.txt")

def main():
    print(f"Testing Azure File mount at: {MOUNT_PATH}")

    # Check that the mount exists
    if not os.path.exists(MOUNT_PATH):
        print(f"❌ Mount path does not exist: {MOUNT_PATH}")
        sys.exit(1)
    else:
        print(f"✅ Mount path exists")

    # Try creating a folder
    try:
        os.makedirs(TEST_DIR, exist_ok=True)
        print(f"✅ Created/verified test directory: {TEST_DIR}")
    except Exception as e:
        print(f"❌ Failed to create directory: {e}")
        sys.exit(1)

    # Try writing a file
    try:
        with open(TEST_FILE, "w") as f:
            f.write("Hello from Azure Container App!\n")
        print(f"✅ Wrote test file: {TEST_FILE}")
    except Exception as e:
        print(f"❌ Failed to write file: {e}")
        sys.exit(1)

    # Try reading the file back
    try:
        with open(TEST_FILE, "r") as f:
            contents = f.read().strip()
        print(f"✅ Read file contents: {contents}")
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        sys.exit(1)

    print("🎉 Azure File share mount test succeeded!")

if __name__ == "__main__":
    main()