"""
Educational implementation of the Hill Cipher using 2x2 matrices.
Demonstrates linear algebra applications in classical cryptography.
"""

def char_to_num(c):
    """Converts a character to its numerical equivalent (A=0, B=1... Z=25)."""
    return ord(c.upper()) - 65

def num_to_char(n):
    """Converts a number back to a character (0=A, 1=B...)."""
    return chr((n % 26) + 65)

def get_determinant(matrix):
    """Calculates the determinant of a 2x2 matrix."""
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]

def mod_inverse(det, mod=26):
    """Finds the modular multiplicative inverse of the determinant."""
    det = det % mod
    for x in range(1, mod):
        if (det * x) % mod == 1:
            return x
    raise ValueError("The matrix determinant has no modular inverse. Invalid key.")

def get_inverse_matrix(matrix, mod=26):
    """Calculates the inverse of a 2x2 matrix modulo 26."""
    det = get_determinant(matrix)
    det_inv = mod_inverse(det, mod)

    # Calculate the adjugate matrix for 2x2
    # [ d, -b ]
    # [-c,  a ]
    adj = [
        [matrix[1][1], -matrix[0][1]],
        [-matrix[1][0], matrix[0][0]]
    ]

    # Multiply adjugate by modular inverse of determinant, modulo 26
    inv_matrix = [
        [(adj[0][0] * det_inv) % mod, (adj[0][1] * det_inv) % mod],
        [(adj[1][0] * det_inv) % mod, (adj[1][1] * det_inv) % mod]
    ]
    return inv_matrix

def multiply_matrix_vector(matrix, vector, mod=26):
    """Multiplies a 2x2 matrix by a 2x1 vector modulo 26."""
    return [
        (matrix[0][0] * vector[0] + matrix[0][1] * vector[1]) % mod,
        (matrix[1][0] * vector[0] + matrix[1][1] * vector[1]) % mod
    ]

def hill_encrypt(plaintext, key_matrix):
    """Encrypts a string using the Hill cipher (2x2 key matrix)."""
    plaintext = plaintext.replace(" ", "").upper()
    
    # Pad with 'X' if the length is odd
    if len(plaintext) % 2 != 0:
        plaintext += 'X'
        
    ciphertext = ""
    for i in range(0, len(plaintext), 2):
        vector = [char_to_num(plaintext[i]), char_to_num(plaintext[i+1])]
        result_vector = multiply_matrix_vector(key_matrix, vector)
        ciphertext += num_to_char(result_vector[0]) + num_to_char(result_vector[1])
        
    return ciphertext

def hill_decrypt(ciphertext, key_matrix):
    """Decrypts a string using the Hill cipher by finding the inverse key matrix."""
    inv_matrix = get_inverse_matrix(key_matrix)
    
    plaintext = ""
    for i in range(0, len(ciphertext), 2):
        vector = [char_to_num(ciphertext[i]), char_to_num(ciphertext[i+1])]
        result_vector = multiply_matrix_vector(inv_matrix, vector)
        plaintext += num_to_char(result_vector[0]) + num_to_char(result_vector[1])
        
    return plaintext

# --- DEMO ---
if __name__ == '__main__':
    print("--- 🔐 Hill Cipher Demonstration ---")

    key = [[9, 4], [5, 7]]
    
    message = "SECURITY"
    print(f"[*] Original Message: {message}")
    print(f"[*] Key Matrix: {key}")
    
    encrypted = hill_encrypt(message, key)
    print(f"[+] Encrypted Message: {encrypted}")
    
    decrypted = hill_decrypt(encrypted, key)
    print(f"[+] Decrypted Message: {decrypted}")
