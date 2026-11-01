# **JWT (JSON Web Tokens) - Complete Guide*

## **1. What is JWT?**
- A **compact, URL-safe** token format for securely transmitting claims between parties.
- Used for **authentication** (replacing sessions) and **secure data exchange**.
- Structure: `Header.Payload.Signature` (e.g., `xxxxx.yyyyy.zzzzz`).

### **JWT Structure**
| Part       | Description                                                                 |
|------------|-----------------------------------------------------------------------------|
| **Header** | Contains token type (`JWT`) and signing algorithm (e.g., `HS256`, `RS256`). |
| **Payload** | Contains claims (user data, expiration, etc.).                             |
| **Signature** | Securely hashes `Header + Payload` using `JWT_SECRET`.                     |

---

## **2. How JWT Works**
1. **User logs in** → Server validates credentials.
2. **Server generates JWT** → Signs it with `JWT_SECRET`.
3. **Client stores JWT** (in cookies/localStorage) and sends it in requests.
4. **Server verifies JWT** → Grants access if valid.

---

## **3. Generating a Secure `JWT_SECRET`**
### **Option 1: Use OpenSSL (Recommended)**
```bash
# Generate a 64-character random secret (HS256)
openssl rand -hex 32
# Example output: 5f4dcc3b5aa765d61d8327deb882cf99b7c64a3f5e5d5d5d5d5d5d5d5d5d5d5d
```
- **Store this in `.env`**:
  ```env
  JWT_SECRET=change_me
  JWT_ALG=HS256
  JWT_EXP_MINUTES=60  # Token expires in 1 hour
  ```

### **Option 2: Use Python**
```python
import secrets
print(secrets.token_hex(32))  # 64-character secret
```

### **Option 3: Use Node.js**
```javascript
require('crypto').randomBytes(32).toString('hex');
```

---

## **4. JWT Best Practices**
| Rule                          | Explanation                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| **Use `HS256` (HMAC-SHA256)** | Best for most apps. Requires a strong `JWT_SECRET`.                        |
| **Keep `JWT_SECRET` private** | Never commit to Git! Use `.env` + environment variables.                   |
| **Set short expiration**      | `JWT_EXP_MINUTES=60` (1 hour) reduces risk if token is stolen.             |
| **Use HTTPS**                 | Prevents man-in-the-middle attacks.                                        |
| **Store securely**            | Use `HttpOnly` cookies (safer than localStorage).                          |

---

## **5. Implementing JWT in FastAPI**
### **Install Dependencies**
```bash
pip install python-jose[cryptography]  # For JWT handling
```

### **FastAPI JWT Example**
```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Config (load from .env)
JWT_SECRET = "your_strong_secret_here"  # Use os.getenv("JWT_SECRET")
JWT_ALG = "HS256"
JWT_EXP_MINUTES = 60

# Create token
def create_jwt(data: dict, expires_delta: timedelta = None):
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXP_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

# Verify token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_jwt(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

# Usage in routes
@app.post("/login")
def login(username: str, password: str):
    # Validate credentials → generate token
    token = create_jwt({"sub": username})
    return {"access_token": token}

@app.get("/protected")
def protected_route(user: dict = Depends(verify_jwt)):
    return {"user": user}
```

---

## **6. Debugging JWT Issues**
| Problem                     | Solution                                                                 |
|-----------------------------|--------------------------------------------------------------------------|
| **Invalid signature**       | Verify `JWT_SECRET` matches on client/server.                           |
| **Token expired**           | Increase `JWT_EXP_MINUTES` or refresh tokens.                           |
| **Algorithm mismatch**      | Ensure `JWT_ALG` (e.g., `HS256`) matches on both sides.                |
| **Not a JWT token**         | Check if the token is correctly formatted (`xxxxx.yyyyy.zzzzz`).       |

---

## **7. Advanced: RSA256 (Public/Private Key)**
For higher security (e.g., microservices), use **asymmetric encryption**:
```bash
# Generate RSA key pair
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
```
- **Private key**: Signs tokens (`JWT_ALG=RS256`).
- **Public key**: Verifies tokens.

---

### **Final Checklist**
1. Generate a strong `JWT_SECRET` (64+ chars, random).
2. Store it in `.env` (never in code).
3. Set a reasonable `JWT_EXP_MINUTES` (e.g., 15–60 mins).
4. Use `HS256` unless you need `RS256`.
5. Always validate tokens server-side.

Need help with a specific JWT implementation? Let me know! 🔐