import zipfile
import itertools
import string
import sys

def crack():
    zip_path = "8week/emergency_storage_key.zip"
    try:
        zf = zipfile.ZipFile(zip_path, 'r')
        target = zf.namelist()[0]
    except Exception as e:
        print("Error opening zip:", e)
        return

    print("Trying numbers only (000000-999999)...")
    for i in range(1000000):
        pwd = f"{i:06d}"
        if i % 100000 == 0:
            print(f"Trying {pwd}...")
        try:
            zf.read(target, pwd=pwd.encode())
            print(f"\nFOUND! Password is: {pwd}")
            return
        except RuntimeError as e:
            if 'password' in str(e).lower():
                continue
        except Exception:
            continue
            
    print("Not a simple 6-digit number.")
crack()
