import random

def gcd(a, b):
    """Calculates the Greatest Common Divisor (GCD)."""
    while b != 0:
        a, b = b, a % b
    return a

def generate_keypair(n=8):
    """
    Generates public and private keys for the Merkle-Hellman cryptosystem.
    n: the number of bits the knapsack can encrypt (block size).
    """
    # 1. Generate a superincreasing knapsack (W)
    # Each element must be greater than the sum of all preceding elements
    W = []
    total = 0
    for _ in range(n):
        val = random.randint(total + 1, total + 10)
        W.append(val)
        total += val
        
    # 2. Choose an integer q strictly greater than the sum of W
    q = random.randint(total + 1, total + 50)
    
    # 3. Choose a multiplier r coprime to q
    r = random.randint(2, q - 1)
    while gcd(r, q) != 1:
        r = random.randint(2, q - 1)
        
    # 4. Create the public key B where B_i = (W_i * r) mod q
    B = [(w * r) % q for w in W]
    
    # Public Key: B | Private Key: (W, q, r)
    return B, (W, q, r)

def encrypt(public_key, binary_message):
    """
    Encrypts a binary message (list of 0s and 1s) using the public knapsack.
    """
    if len(public_key) != len(binary_message):
        raise ValueError("Message length must match the public key size.")
    
    # Ciphertext is the sum of (B_i * bit_i)
    ciphertext = sum(b * m for b, m in zip(public_key, binary_message))
    return ciphertext

def decrypt(private_key, ciphertext):
    """
    Decrypts the ciphertext using the private key components.
    """
    W, q, r = private_key
    
    # 1. Find the modular inverse of r modulo q
    r_inv = pow(r, -1, q)
    
    # 2. Calculate the original target sum: C' = (C * r_inv) mod q
    c_prime = (ciphertext * r_inv) % q
    
    # 3. Solve the subset sum problem using the superincreasing knapsack
    # start from the largest element
    binary_message = []
    for w in reversed(W):
        if c_prime >= w:
            binary_message.insert(0, 1)
            c_prime -= w
        else:
            binary_message.insert(0, 0)
            
    return binary_message

# ==========================================
# ALGORITHM DEMONSTRATION
# ==========================================
if __name__ == '__main__':
    print("--- Merkle-Hellman Knapsack Demonstration ---")
    
    # Block size of 8 bits (1 byte)
    block_size = 8
    
    # 1. Key Generation
    public_key, private_key = generate_keypair(block_size)
    print(f"[+] Public Key (B): {public_key}")
    print(f"[+] Private Key (W, q, r): {private_key}")
    
    # 2. Encryption
    # An 8-bit binary message (e.g., representing an ASCII character)
    original_message = [0, 1, 1, 0, 1, 0, 0, 1] 
    print(f"\n[!] Original binary message: {original_message}")
    
    encrypted_msg = encrypt(public_key, original_message)
    print(f"[+] Encrypted message (Ciphertext sum): {encrypted_msg}")
    
    # 3. Decryption
    decrypted_msg = decrypt(private_key, encrypted_msg)
    print(f"[+] Decrypted binary message: {decrypted_msg}")
