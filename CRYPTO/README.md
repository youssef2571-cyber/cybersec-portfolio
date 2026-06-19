# 🔐 Cryptography & Engineering Portfolio

This directory serves as a comprehensive portfolio of cryptographic implementations developed during my academic curriculum. The focus is on understanding the deep mathematical foundations, structural designs, and algorithmic vulnerabilities of various cryptographic systems, rather than simply using black-box libraries.

## 📂 Repository Architecture

The projects are logically categorized into Asymmetric, Symmetric, and Classical cryptographic systems.

### 🔑 1. Asymmetric Cryptography (Public-Key)
Implementations relying on computational hardness assumptions (factorization, discrete logarithms, and subset-sum problems).
* **`RSA/`**: A complete suite of Bash scripts for key generation, encryption, decryption, and digital signatures.
* **`ECC/`**: Elliptic Curve Cryptography implementation over a finite field, showcasing the Double-and-Add algorithm for scalar multiplication.
* **`elgamal/`**: Python implementation based on the Diffie-Hellman key exchange and the Discrete Logarithm Problem.
* **`merkle_hellman/`**: An exploration of the historical Knapsack cryptosystem based on superincreasing sequences.

### 🛡️ 2. Symmetric Cryptography (Block Ciphers)
Exploration of symmetric structures from legacy Feistel networks to modern Substitution-Permutation Networks (SPN).
* **`AES/`**: Structural demonstration of the Advanced Encryption Standard, highlighting the four core operations (SubBytes, ShiftRows, MixColumns, AddRoundKey).
* **`DES&3DES/`**: Core implementations of the Feistel Network and the Encrypt-Decrypt-Encrypt (EDE) process used in Triple DES.
* **`modes_operatoires/`**: Demonstrations of how block ciphers process data streams, including ECB, CBC (with Initialization Vectors), and CTR modes.

### 🏛️ 3. Classical Cryptography
* **`HILL/`**: A polygraphic substitution cipher implementation demonstrating the application of linear algebra (2x2 matrix operations and modular inverses) in cryptography.

## 🛠️ Technical Stack & Concepts
* **Languages:** Python (Algorithmic logic, Math), Bash / Shell Scripting (Automation).
* **Core Mathematics:** Modular Arithmetic, Finite Fields (Galois), Matrix Algebra, Prime Number Generation, Extended Euclidean Algorithm.
* **Security Concepts:** Diffusion & Confusion, Padding, Initialization Vectors (IV), Key Spaces.

## ⚠️ Academic Disclaimer
These scripts are written from scratch to demonstrate the mathematical and structural mechanics of cryptographic algorithms. They are intended strictly for **educational and academic evaluation**. For production environments, always rely on vetted, standardized cryptographic libraries (such as OpenSSL or libsodium).
