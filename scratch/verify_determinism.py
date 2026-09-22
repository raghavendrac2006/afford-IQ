import os, hashlib, subprocess, sys

repo_root = r"a:\Hackerrank"
out1_path = os.path.join(repo_root, "output.csv")

# First run
subprocess.run([sys.executable, os.path.join(repo_root, "code", "main.py")], check=True)

with open(out1_path, "rb") as f:
    bytes1 = f.read()

hash1 = hashlib.sha256(bytes1).hexdigest()
size1 = len(bytes1)
lines1 = bytes1.decode('utf-8').count('\n') + (1 if not bytes1.endswith(b'\n') else 0)

# Second run
subprocess.run([sys.executable, os.path.join(repo_root, "code", "main.py")], check=True)

with open(out1_path, "rb") as f:
    bytes2 = f.read()

hash2 = hashlib.sha256(bytes2).hexdigest()
size2 = len(bytes2)

print(f"Run 1 File Size: {size1} bytes | Lines: {lines1} | SHA-256: {hash1}")
print(f"Run 2 File Size: {size2} bytes | SHA-256: {hash2}")
print(f"Byte-for-byte identical: {bytes1 == bytes2}")
print(f"SHA-256 Match: {hash1 == hash2}")
