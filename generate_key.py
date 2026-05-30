import hashlib

#  يجب أن يطابق SECRET_SALT في license_manager.py
SECRET_SALT = "CRM_Pro_Commercial_2026_SecretKey"

device_id = input("Enter the client Device ID: ").strip()
if not device_id:
    print("Error: No Device ID provided.")
    exit()

key = hashlib.sha256((device_id + SECRET_SALT).encode()).hexdigest()[:16].upper()
print("\n Activation Key for this device:")
print("-" * 30)
print(f"{key[:4]}-{key[4:8]}-{key[8:12]}-{key[12:]}")
print("-" * 30)