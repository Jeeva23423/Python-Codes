import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

# Get the encrypted file path from the user
encrypted_file_path = input("Enter the encrypted file path to decrypt: ")
decrypted_file_path = encrypted_file_path.replace(".enc", "")

try:
    # Read the stored encryption key and IV
    with open("key_iv.bin", "rb") as key_file:
        key_data = key_file.read()
        KEY = key_data[:32]  # First 32 bytes = AES key
        IV = key_data[32:]   # Last 16 bytes = IV

    # Read encrypted data
    with open(encrypted_file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()

    # Decrypt the data
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

    # Remove padding
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

    # Write the decrypted file (keeping original format)
    with open(decrypted_file_path, "wb") as decrypted_file:
        decrypted_file.write(decrypted_data)

    # Delete the encrypted file after successful decryption
    os.remove(encrypted_file_path)

    print(f"File decrypted successfully. Decrypted file saved as {decrypted_file_path}.")
    print(f"Encrypted file {encrypted_file_path} has been deleted.")

except Exception as e:
    print(f"An error occurred during decryption: {e}")
