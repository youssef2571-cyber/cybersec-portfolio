# 🌐 Secure Web Application Development (PHP)

This repository contains the source code for a dynamic Event Management Platform. In the context of cybersecurity, this project serves as a demonstration of **Secure Coding Practices** and **Application Security (AppSec)** principles. 

Understanding how web applications handle sessions, databases, and user inputs is critical for effectively auditing code and deploying Web Application Firewalls (WAF).

## 🛡️ Security Features Implemented

### 1. Identity and Access Management (IAM)
* **Session Management:** Secure initialization and destruction of user sessions (`session_destroy()`) to prevent session fixation and hijacking.
* **Role-Based Access Control (RBAC):** Strict routing logic ensuring that unauthenticated users are forcefully redirected to the login gateway. Administrative functions (CRUD operations on events) validate the `$_SESSION['role']` before execution, preventing vertical privilege escalation.

### 2. Input Sanitization & Output Encoding
* **XSS Mitigation:** Comprehensive use of `htmlspecialchars()` on all user-generated content retrieved from the database before rendering it in the DOM, neutralizing Reflected and Stored Cross-Site Scripting (XSS) vectors.
* **Strict Type Casting & Routing:** The application relies on strict whitelist routing (`in_array($page, ['login', ...])`) to prevent Local File Inclusion (LFI) or unauthorized directory traversal attempts via the `page` GET parameter.

### 3. Database Security
* *Note: The architecture relies on an external `connexion.php` module, designed to isolate database credentials and enforce secure PDO/MySQLi connection states (such as Prepared Statements to prevent SQL Injection).*

## 🛠️ Technical Stack
* **Backend:** PHP 8.x
* **Database:** MySQL / MariaDB
* **Frontend:** HTML5, CSS3
* **Security Concepts:** RBAC, Session Handling, XSS Prevention, Authentication Logic.
