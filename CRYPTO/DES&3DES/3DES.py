"""
3DES (Triple DES) implementation.
Uses the EDE (Encrypt-Decrypt-Encrypt) mechanism.
"""
from des import des_encrypt # Import de la structure de base

def triple_des_encrypt(L, R, K1, K2, K3):
    """
    3DES implementation using the EDE process.
    """
    # 1. Encrypt with K1
    L1, R1 = des_encrypt(L, R, [K1, K1]) 
    
    # 2. Decrypt with K2 
    # (In Feistel, decryption is done by reversing the order of keys)
    L2, R2 = des_encrypt(L1, R1, [K2, K2]) 
    
    # 3. Encrypt with K3
    L3, R3 = des_encrypt(L2, R2, [K3, K3])
    
    return L3, R3

# --- DEMO ---
if __name__ == '__main__':
    L, R = "1010", "1100"
    K1, K2, K3 = "0011", "0101", "1110"
    L_3des, R_3des = triple_des_encrypt(L, R, K1, K2, K3)
    print(f"3DES Result: L={L_3des}, R={R_3des}")
