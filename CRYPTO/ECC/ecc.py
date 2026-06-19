# ECC - Elliptic Curve Cryptography (Simplified for educational purposes)
# Working with curves of the form: y^2 = x^3 + a*x + b (mod p)

def inverse_mod(k, p):
    """Computes the modular multiplicative inverse using Fermat's Little Theorem."""
    return pow(k, p - 2, p)

def point_add(P, Q, a, p):
    """Adds two points P and Q on the elliptic curve."""
    if P is None: return Q
    if Q is None: return P
    
    x1, y1 = P
    x2, y2 = Q
    
    if x1 == x2 and y1 != y2:
        return None # Point at infinity
    
    if x1 == x2: # Point doubling
        m = (3 * x1**2 + a) * inverse_mod(2 * y1, p)
    else: # Point addition
        m = (y2 - y1) * inverse_mod(x2 - x1, p)
    
    x3 = (m**2 - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)

def scalar_mult(k, P, a, p):
    """Multiplies point P by scalar k using Double-and-Add algorithm."""
    result = None
    addend = P
    while k:
        if k & 1:
            result = point_add(result, addend, a, p)
        addend = point_add(addend, addend, a, p)
        k >>= 1
    return result

# ==========================================
#  ECC DEMONSTRATION
# ==========================================
if __name__ == '__main__':
    # Curve: y^2 = x^3 + 2x + 2 (mod 17) -> a=2, b=2, p=17
    a, b, p = 2, 2, 17
    G = (5, 1) # Generator point
    
    print("---  ECC Demonstration ---")
    # Private Key: random integer d
    d = 3 
    # Public Key: Q = d * G
    Q = scalar_mult(d, G, a, p)
    
    print(f"[+] Private Key (d): {d}")
    print(f"[+] Public Key (Q): {Q}")
