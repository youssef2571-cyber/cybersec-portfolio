# 🏛️ Classical Cryptography: The Hill Cipher

This directory contains an implementation of the **Hill Cipher**, a polygraphic substitution cipher based on linear algebra. Invented by Lester S. Hill in 1929, it was one of the first practical ciphers to operate on blocks of letters simultaneously.

## 🧠 Mathematical Foundation

The Hill cipher uses matrix multiplication and modular arithmetic to transform plaintext into ciphertext.

### 1. The Key
The key is an $n \times n$ matrix (in this implementation, a $2 \times 2$ matrix). 
To be a valid key, the matrix must be **invertible modulo 26** (the size of the English alphabet). This means the determinant of the key matrix must be coprime to 26 ($\gcd(\det(K), 26) = 1$).

### 2. Encryption
The plaintext is divided into vectors $P$ of length $n$. The encryption process is a linear transformation:
$$C \equiv K \cdot P \pmod{26}$$
Where:
* $C$ is the ciphertext vector.
* $K$ is the key matrix.
* $P$ is the plaintext vector.

### 3. Decryption
To reverse the process, we must calculate the inverse of the key matrix $K^{-1}$ modulo 26.
$$P \equiv K^{-1} \cdot C \pmod{26}$$

Calculating $K^{-1}$ involves finding the modular multiplicative inverse of the determinant and multiplying it by the adjugate matrix.

## 🚀 Technical Highlights
* **Pure Algorithmic Logic:** This implementation avoids external math libraries (like NumPy) to explicitly demonstrate the underlying algorithms for calculating modular determinants, adjugate matrices, and modular inverses from scratch.
* **Polygraphic Resistance:** Unlike simple substitution ciphers (Caesar, Vigenère), the Hill cipher encrypts multiple letters at once, completely masking single-letter frequencies and making basic frequency analysis impossible.
