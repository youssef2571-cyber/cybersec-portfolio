"""
DES (Data Encryption Standard) core structure.
This implementation demonstrates the Feistel Network used in block ciphers.
"""

def xor(a, b):
    return ''.join(str(int(x) ^ int(y)) for x, y in zip(a, b))

def f_function(R, K):
    """
    Placeholder for the round function (usually involves expansion, 
    S-Boxes and Permutation in real DES).
    """
    return xor(R, K)

def feistel_round(L, R, K):
    """Core Feistel process: one round of processing."""
    new_R = xor(L, f_function(R, K))
    return R, new_R

def des_encrypt(L, R, keys):
    """Encrypts data block using a series of round keys."""
    for K in keys:
        L, R = feistel_round(L, R, K)
    # Final swap for standard Feistel structure
    return R, L

# --- DEMO ---
if __name__ == '__main__':
    # Exemple avec 2 clés de round
    L, R = "1010", "1100"
    keys = ["0011", "0101"]
    L_enc, R_enc = des_encrypt(L, R, keys)
    print(f"DES Result: L={L_enc}, R={R_enc}")
