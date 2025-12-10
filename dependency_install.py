"""
Auto-install dependencies from requirements.txt
Cross-platform: Windows, Linux, macOS, Git Bash, WSL

NOTE: Python must be installed on your PATH
"""

import subprocess
import sys
import os


def main():
    """
    Main function to auto-install Python dependencies from requirements.txt. Changes to the script directory,
    upgrades pip, and installs all packages listed in requirements.txt. Exits with an error if the file is missing.
    """
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print(f"Error: {req_file} not found in {project_dir}")
        sys.exit(1)

    # Upgrade pip first
    print("Upgrading pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    # Install requirements
    print(f"Installing dependencies from {req_file}...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)

    print("\nAll dependencies installed successfully!")

if __name__ == "__main__":
    main()