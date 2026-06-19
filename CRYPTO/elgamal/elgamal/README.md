# 🔐 ElGamal Cryptosystem Implementation

This directory contains a Python implementation of the **ElGamal encryption algorithm**. ElGamal is an asymmetric key encryption algorithm for public-key cryptography which is based on the Diffie-Hellman key exchange. 

The primary objective of this project is to demonstrate the underlying mathematical mechanics of the algorithm, specifically focusing on the **Discrete Logarithm Problem (DLP)** and modular arithmetic, built entirely from scratch.

## 🧠 Mathematical Foundation

The security of ElGamal relies on the computational difficulty of calculating discrete logarithms in a cyclic group.

### 1. Key Generation
* Choose a large prime number $p$ and a generator $g$ of the multiplicative group $\mathbb{Z}_p^*$.
* Select a random private key $x$ such that $1 < x < p-1$.
* Calculate the public key component $y$ using modular exponentiation:
  $$y = g^x \bmod p$$
* **Public Key:** $(p, g, y)$
* **Private Key:** $x$

### 2. Encryption
To encrypt a message $m$ (where $m < p$):
* Choose a random ephemeral key $k$ such that $\gcd(k, p-1) = 1$.
* Compute the shared ephemeral component $c_1$:
  $$c_1 = g^k \bmod p$$
* Compute the masked message $c_2$:
  $$c_2 = m \cdot y^k \bmod p$$
* The resulting ciphertext is the pair $(c_1, c_2)$.

### 3. Decryption
To decrypt the ciphertext $(c_1, c_2)$ using the private key $x$:
* Calculate the shared secret $s$:
  $$s = c_1^x \bmod p$$
* Calculate the modular inverse of $s$, denoted as $s^{-1}$.
* Recover the original message $m$:
  $$m = c_2 \cdot s^{-1} \bmod p$$

## 🚀 Usage

The implementation is contained within `elgamal.py`. It includes functional blocks for key generation, encryption, and decryption, along with a demonstration routine.

### Prerequisites
* Python 3.8+ (Utilizes native modular inverse via `pow()`).
* No external libraries are required (only the built-in `random` module).

### Running the Script
Execute the script directly from your terminal to run the demonstration:

```bash
python3 elgamal.py
