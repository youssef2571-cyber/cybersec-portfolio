import random

def gcd(a, b):
    """Calculates the Greatest Common Divisor (GCD)."""
    while b != 0:
        a, b = b, a % b
    return a

def is_prime(num):
    """Basic primality test for demonstration purposes."""
    if num < 2:
        return False
    for i in range(2, int(num ** 0.5) + 1):
        if num % i == 0:
            return False
    return True

def generate_keypair(p, q):
    """
    Generates the public and private keys from two prime numbers.
    Returns: (public_key, private_key)
    """
    if not (is_prime(p) and is_prime(q)):
        raise ValueError("Both numbers must be prime.")
    elif p == q:
        raise ValueError("p and q cannot be equal.")

    # n = p * q
    n = p * q

    # phi is the Euler's totient of n
    phi = (p - 1) * (q - 1)

    # Choose an integer e such that e and phi(n) are coprime
    e = random.randrange(1, phi)
    g = gcd(e, phi)
    while g != 1:
        e = random.randrange(1, phi)
        g = gcd(e, phi)

    # Use Python's built-in pow() to find the modular inverse of e
    # d * e = 1 mod phi
    d = pow(e, -1, phi)

    # Public key is (e, n) and private key is (d, n)
    return ((e, n), (d, n))

def encrypt(public_key, plaintext):
    """Encrypts an integer message using the public key."""
    e, n = public_key
    # Ciphertext c = m^e mod n
    ciphertext = pow(plaintext, e, n)
    return ciphertext

def decrypt(private_key, ciphertext):
    """Decrypts a ciphertext using the private key."""
    d, n = private_key
    # Plaintext m = c^d mod n
    plaintext = pow(ciphertext, d, n)
    return plaintext

# ==========================================
# ALGORITHM DEMONSTRATION
# ==========================================
if __name__ == '__main__':
    print("---  RSA Cryptosystem Demonstration ---")
    
    # Two prime numbers (in practice, these should be 2048-bit or 4096-bit primes)
    p = 61
    q = 53
    print(f"[*] Chosen primes: p={p}, q={q}")
    
    # 1. Key Generation
    public_key, private_key = generate_keypair(p, q)
    print(f"[+] Public Key (e, n): {public_key}")
    print(f"[+] Private Key (d, n): {private_key}")
    
    # 2. Encryption
    # The message must be an integer smaller than n (n = p * q = 3233)
    message = 1337
    print(f"\n[!] Original message: {message}")
    
    encrypted_msg = encrypt(public_key, message)
    print(f"[+] Encrypted message: {encrypted_msg}")
    
    # 3. Decryption
    decrypted_msg = decrypt(private_key, encrypted_msg)
    print(f"[+] Decrypted message: {decrypted_msg}")
