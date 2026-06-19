# 📉 Elliptic Curve Cryptography (ECC)

This directory contains an educational implementation of ECC over a finite field. ECC is the cornerstone of modern secure communication, providing high security with significantly smaller key sizes compared to RSA.

## 🧠 Core Mathematical Concepts

### 1. The Elliptic Curve
Defined by the Weierstrass equation:
$$y^2 \equiv x^3 + ax + b \pmod{p}$$
Security relies on the **Elliptic Curve Discrete Logarithm Problem (ECDLP)**: Given points $G$ and $Q = dG$, it is computationally infeasible to find the scalar $d$.

### 2. Point Operations
* **Point Addition:** Geometrically, adding two points $P$ and $Q$ to find a third point $R$.
* **Point Doubling:** Adding a point to itself ($2P$).
* **Scalar Multiplication:** Repeated addition ($kP$) using the "Double-and-Add" algorithm, which provides $O(\log k)$ efficiency.

## 🚀 Key Advantages
* **Efficiency:** Smaller keys lead to faster computations and less power consumption (ideal for mobile and embedded systems).
* **Robustness:** No known sub-exponential algorithm exists to solve the ECDLP, unlike the General Number Field Sieve for integer factorization in RSA.

## 🛠️ Implementation Highlights
* Implements the **Double-and-Add** algorithm for efficient scalar multiplication.
* Handles modular arithmetic over finite fields $\mathbb{F}_p$.
