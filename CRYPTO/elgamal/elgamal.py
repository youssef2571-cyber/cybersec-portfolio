import random

def gcd(a, b):
    """Calculates the Greatest Common Divisor (GCD)."""
    while b != 0:
        a, b = b, a % b
    return a

def generate_elgamal_keys(p, g):
    """
    Generates the public and private keys.
    p : a large prime number
    g : a generator of the multiplicative group
    """
    # Private key (x): a random integer between 1 and p-2
    x = random.randint(1, p - 2)
    
    # Public key (y): y = g^x mod p
    y = pow(g, x, p)
    
    return (p, g, y), x  # Returns (Public Key, Private Key)

def encrypt(public_key, msg):
    """Encrypts a message (as an integer) using the public key."""
    p, g, y = public_key
    
    # Choose a random ephemeral key k such that gcd(k, p-1) == 1
    k = random.randint(1, p - 2)
    while gcd(k, p - 1) != 1:
        k = random.randint(1, p - 2)

    # c1 = g^k mod p (shared part)
    c1 = pow(g, k, p)
    
    # c2 = msg * y^k mod p (masked message)
    c2 = (msg * pow(y, k, p)) % p
    
    return c1, c2

def decrypt(private_key, p, c1, c2):
    """Decrypts the ciphertext (c1, c2) using the private key."""
    x = private_key
    
    # Step 1: Calculate the shared secret s = c1^x mod p
    s = pow(c1, x, p)
    
    # Step 2: Calculate the modular inverse of s
    # (pow handles native modular inverse with a negative exponent in Python 3.8+)
    s_inv = pow(s, -1, p) 
    
    # Step 3: Recover the message msg = c2 * s_inv mod p
    msg = (c2 * s_inv) % p
    return msg

# ==========================================
#  ALGORITHM DEMONSTRATION
# ==========================================
if __name__ == "__main__":
    print("---  ElGamal Demonstration ---")
    
    # Public parameters (in reality, p should be a massive prime number)
    p_prime = 467 
    g_generator = 2 
    
    # 1. Key Generation
    pub_key, priv_key = generate_elgamal_keys(p_prime, g_generator)
    print(f"[+] Public Key (p, g, y): {pub_key}")
    print(f"[+] Private Key (x): {priv_key}")
    
    # 2. Encryption
    message_original = 1337 # The message must be an integer < p
    print(f"\n[!] Original message: {message_original}")
    c1, c2 = encrypt(pub_key, message_original)
    print(f"[+] Encrypted message (c1, c2): ({c1}, {c2})")
    
    # 3. Decryption
    message_decrypted = decrypt(priv_key, p_prime, c1, c2)
    print(f"[+] Decrypted message: {message_decrypted}")
