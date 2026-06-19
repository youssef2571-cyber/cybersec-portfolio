"""
Block Cipher Modes of Operation & Feistel Networks.
Educational implementation of ECB, CBC, CTR modes, and a Feistel structure.
"""

def xor(a, b):
    """Performs bitwise XOR operation between two binary strings."""
    return ''.join(str(int(x) ^ int(y)) for x, y in zip(a, b))

# =========================
# ECB (Electronic Codebook)
# =========================
def ecb_encrypt(blocks, key):
    """ECB Mode: Each block is encrypted independently."""
    return [xor(b, key) for b in blocks]

# =========================
# CBC (Cipher Block Chaining)
# =========================
def cbc_encrypt(blocks, key, iv):
    """CBC Mode: Each block is XORed with the previous ciphertext block."""
    result = []
    prev = iv
    for b in blocks:
        x = xor(b, prev)
        c = xor(x, key)
        result.append(c)
        prev = c
    return result

# =========================
# CTR (Counter Mode)
# =========================
def increment(counter):
    """Increments a binary counter."""
    return format((int(counter, 2) + 1) % (2**len(counter)), f'0{len(counter)}b')

def ctr_encrypt(blocks, key, counter):
    """CTR Mode: Encrypts a counter and XORs the result with the plaintext."""
    result = []
    ctr = counter
    for b in blocks:
        keystream = xor(ctr, key)
        c = xor(b, keystream)
        result.append(c)
        ctr = increment(ctr)
    return result

# =========================
# FEISTEL NETWORK (2 Rounds)
# =========================
def feistel_encrypt(L, R, K1, K2):
    """
    Feistel Network structure with 2 rounds.
    L, R: Left and Right halves of the data
    K1, K2: Round keys
    """
    # Round 1
    L1 = R
    R1 = xor(L, xor(R, K1))
    # Round 2
    L2 = R1
    R2 = xor(L1, xor(R1, K2))
    return L2, R2
