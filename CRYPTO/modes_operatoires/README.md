## 🧱 Block Cipher Modes & Feistel Networks

This module demonstrates fundamental block cipher modes used to extend the utility of basic encryption algorithms.

### Modes of Operation
* **ECB (Electronic Codebook):** The simplest mode. Each block is encrypted independently. Note: Not secure for patterns in data.
* **CBC (Cipher Block Chaining):** Adds an Initialization Vector (IV) and links blocks. Each plaintext block is XORed with the previous ciphertext block before encryption, ensuring identical plaintext blocks result in different ciphertexts.
* **CTR (Counter Mode):** Transforms a block cipher into a stream cipher. It encrypts an incrementing counter, creating a keystream that is XORed with the plaintext.

### Feistel Network
A symmetric structure used in the construction of block ciphers (like DES). It splits the data into two halves and applies a round function iteratively using subkeys. This ensures that the encryption process is reversible, even if the round function itself is not.
