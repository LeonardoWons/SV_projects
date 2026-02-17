import os
import subprocess
import sys

for filename in os.listdir("req"):
    package_path = os.path.join("req", filename)
    print(package_path)
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_path])
