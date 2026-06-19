
# 🎒 Merkle-Hellman Knapsack Cryptosystem

This directory contains a Python implementation of the **Merkle-Hellman Knapsack Cryptosystem**. It is one of the first asymmetric key cryptosystems ever developed, based on the **Subset Sum Problem** (also known as the Knapsack Problem).

## 🧠 Mathematical Foundation

Unlike RSA or ElGamal, which rely on prime factorization or discrete logarithms, this system uses the computational difficulty of solving the subset sum problem.

### 1. Key Generation
* **Private Key:** A superincreasing sequence $W = \{w_1, w_2, \dots, w_n\}$, where each element is greater than the sum of all preceding elements, along with a modulus $q$ and a multiplier $r$.
* **Public Key:** A "scrambled" sequence $B = \{b_1, b_2, \dots, b_n\}$ where $b_i = (w_i \cdot r) \bmod q$.
* The sequence $B$ appears random, making it difficult for an attacker to determine the original sequence $W$.

### 2. Encryption
To encrypt a binary message $M$ of length $n$:
* Compute the ciphertext $C$ as the dot product of the public key $B$ and the message vector $M$:
  $$C = \sum_{i=1}^{n} b_i \cdot m_i$$

### 3. Decryption
To decrypt $C$ using the private key $(W, q, r)$:
* Calculate the target sum $C'$ using the modular inverse of $r$:
  $$C' = (C \cdot r^{-1}) \bmod q$$
* Since $W$ is superincreasing, solve for $M$ using a greedy algorithm:
  * For $i$ from $n$ down to $1$:
    * If $C' \ge w_i$, then $m_i = 1$ and $C' = C' - w_i$.
    * Else, $m_i = 0$.

## 🚀 Usage

The implementation is contained within `merkle_hellman.py`. It includes functions for key pair generation, encryption, and the greedy decryption algorithm.

### Running the Script
Execute the script directly from your terminal to run the demonstration:

```bash
python3 merkle_hellman.py
