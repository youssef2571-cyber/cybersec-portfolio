# 🛡️ Symmetric Block Ciphers: From DES to 3DES

This directory explores the evolution of symmetric-key cryptography through the Feistel network architecture.

## 1. DES (Data Encryption Standard)
The DES algorithm introduced the use of the **Feistel Network**, a design that divides data into two halves and applies round functions to ensure confusion and diffusion.



## 2. 3DES (Triple DES)
As brute-force capabilities increased, the 56-bit key of DES became insufficient. 3DES was developed as a robust evolution using the **EDE (Encrypt-Decrypt-Encrypt)** process.

### The EDE Logic:
- **Encrypt** with $K_1$
- **Decrypt** with $K_2$
- **Encrypt** with $K_3$

*Note: This process remains backward compatible with standard DES if $K_1=K_2=K_3$.*



## ⚠️ Academic Note
DES and 3DES are legacy standards. They are provided here strictly for **educational purposes** to understand Feistel structures. Modern applications should use **AES**.
