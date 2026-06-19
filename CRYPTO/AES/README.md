## AES (The Modern Standard)
* **AES (`aes.py`):** The Advanced Encryption Standard (Rijndael) is the current global standard. It abandoned the Feistel network in favor of a **Substitution-Permutation Network (SPN)**.
* AES operates on a 4x4 column-major order matrix of bytes (the *State*).

### The Four Core Operations of an AES Round:
1. **SubBytes:** A non-linear substitution step using a lookup table (S-box) to achieve *confusion*.
2. **ShiftRows:** A transposition step where rows of the state are shifted cyclically to achieve *diffusion*.
3. **MixColumns:** A linear mixing operation acting on the columns, using Galois Field $\text{GF}(2^8)$ mathematics for profound *diffusion*.
4. **AddRoundKey:** The state is XORed with a subkey derived from the main key schedule.

## ⚠️ Academic Note
While the DES/3DES scripts represent complete logical flows, the AES implementation is provided as a structural demonstration of its internal rounds. In real-world applications, **always** use vetted cryptographic libraries (like `OpenSSL` or Python's `cryptography` module) for AES implementations to avoid side-channel attacks.
