# Logging Best Practices: Where and How to Log

## ⚠️ The Short Answer: **Don't log in every function!**

Logging in every function will negatively impact your project in several ways. Here's why and where you should actually log:

## 🚫 Problems with Logging in Every Function

### 1. **Performance Impact**
```python
# BAD: This creates unnecessary overhead
def process_user(user):
    logger.debug(f"Entering process_user with {user}")  # ❌ Don't do this!
    result = do_something(user)
    logger.debug(f"Exiting process_user with {result}") # ❌ Don't do this!
    return result
```

### 2. **Log Spam and Noise**
- Your logs become unreadable
- Important messages get buried in noise
- Hard to find actual issues

### 3. **Maintenance Nightmare**
- Changing log messages requires modifying many functions
- Hard to maintain consistent logging patterns

### 4. **Security Risks**
- Might accidentally log sensitive data
- More places where data leakage can occur

---

## ✅ Where You SHOULD Log

### 1. **Entry/Exit Points of Major Operations**
```python
def process_order(order_id):
    """Process a customer order"""
    logger.info(f"Starting order processing for order_id: {order_id}")
    
    try:
        # Business logic here (no logging inside these helper functions)
        validate_order(order_id)
        process_payment(order_id)
        update_inventory(order_id)
        send_confirmation(order_id)
        
        logger.info(f"Order {order_id} processed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process order {order_id}: {str(e)}")
        return False

# Helper functions - NO LOGGING here
def validate_order(order_id):
    # Just business logic, no logging
    if not order_exists(order_id):
        raise ValueError("Order does not exist")
    return True
```

### 2. **Decision Points and Branching Logic**
```python
def calculate_discount(user_type, order_amount):
    """Calculate discount based on user type and order amount"""
    
    if user_type == "premium":
        discount = order_amount * 0.2
        logger.debug(f"Applied 20% premium discount: ${discount}")
    elif user_type == "vip":
        discount = order_amount * 0.3
        logger.debug(f"Applied 30% VIP discount: ${discount}")
    else:
        discount = 0
        logger.debug("No discount applied for regular user")
    
    return discount
```

### 3. **External Calls and I/O Operations**
```python
def fetch_user_data(user_id):
    """Fetch user data from external API"""
    logger.info(f"Fetching data for user {user_id} from API")
    
    try:
        response = requests.get(f"{API_URL}/users/{user_id}", timeout=10)
        response.raise_for_status()
        
        logger.debug(f"API response received: {response.status_code}")
        return response.json()
        
    except requests.Timeout:
        logger.warning(f"API timeout for user {user_id}")
        return None
    except requests.RequestException as e:
        logger.error(f"API error for user {user_id}: {str(e)}")
        return None
```

### 4. **Error Handling and Exception Blocks**
```python
def update_database_record(record_id, data):
    """Update a database record"""
    try:
        result = db_session.execute(update_query, data)
        db_session.commit()
        return result
        
    except DatabaseError as e:
        logger.error(f"Database update failed for record {record_id}: {str(e)}")
        logger.debug(f"Failed data: {data}")  # Detailed debug info
        db_session.rollback()
        raise
```

### 5. **State Changes and Important Events**
```python
def change_user_status(user_id, new_status):
    """Change user account status"""
    old_status = get_current_status(user_id)
    
    if old_status != new_status:
        logger.info(f"Changing user {user_id} status from {old_status} to {new_status}")
        update_status_in_db(user_id, new_status)
        
        if new_status == "suspended":
            logger.warning(f"User {user_id} account suspended")
```

---

## 🎯 Practical Logging Strategy by Layer

### **Controller/API Layer** (Most logging here)
```python
# app/controllers/user_controller.py
@router.post("/users")
async def create_user(user_data: UserCreate):
    logger.info(f"Creating new user: {user_data.email}")
    
    try:
        user = await user_service.create_user(user_data)
        logger.info(f"User created successfully: {user.id}")
        return user
        
    except EmailAlreadyExistsError:
        logger.warning(f"Email already exists: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already exists")
    except Exception as e:
        logger.error(f"Unexpected error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### **Service Layer** (Moderate logging)
```python
# app/services/user_service.py
async def create_user(user_data: UserCreate):
    logger.debug(f"Validating user data for: {user_data.email}")
    
    if await user_repository.email_exists(user_data.email):
        raise EmailAlreadyExistsError()
    
    logger.debug("Creating user in database")
    user = await user_repository.create(user_data)
    
    logger.debug("Sending welcome email")
    await email_service.send_welcome_email(user.email)
    
    return user
```

### **Repository/DAO Layer** (Minimal logging)
```python
# app/repositories/user_repository.py
async def create(self, user_data: UserCreate):
    # Only log database-specific issues
    try:
        query = "INSERT INTO users (...) VALUES (...) RETURNING *"
        result = await self.db.execute(query, user_data.dict())
        return result
    except DatabaseError as e:
        logger.error(f"Database error creating user: {str(e)}")
        raise
```

### **Utility/Helper Functions** (Almost no logging)
```python
# app/utils/validation.py
def validate_email_format(email: str) -> bool:
    # No logging here - pure function
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```

---

## 📊 Logging Level Strategy

| Layer | DEBUG | INFO | WARNING | ERROR |
|-------|-------|------|---------|-------|
| **Controller** | Rarely | ✅ Entry/exit points | ✅ Client errors | ✅ Server errors |
| **Service** | ✅ Complex logic | ✅ Major steps | ✅ Business warnings | ✅ Service errors |
| **Repository** | ✅ Query details | Rarely | ❌ | ✅ DB errors |
| **Utility** | ❌ | ❌ | ❌ | ❌ |

---

## 🏆 Best Practices Summary

### **DO Log:**
- ✅ Entry/exit points of major functions
- ✅ External API calls and I/O operations  
- ✅ Important business decisions
- ✅ Error and exception handling
- ✅ State changes and significant events
- ✅ Performance-critical operations

### **DON'T Log:**
- ❌ Every function call
- ❌ Pure helper functions
- ❌ Simple getter/setter methods
- ❌ Inside tight loops
- ❌ Performance-critical code paths
- ❌ Where sensitive data might be exposed

### **Good Example:**
```python
def process_order_workflow(order_id):
    """Main order processing workflow - OK to log here"""
    logger.info(f"Starting order workflow for {order_id}")
    
    try:
        # These functions should NOT have their own logging
        validate_order(order_id)          # ❌ No logging inside
        charge_payment(order_id)          # ❌ No logging inside  
        update_inventory(order_id)        # ❌ No logging inside
        send_notifications(order_id)      # ❌ No logging inside
        
        logger.info(f"Order {order_id} completed successfully")
        return True
        
    except PaymentError as e:
        logger.warning(f"Payment failed for order {order_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing order {order_id}: {e}")
        return False
```

This approach gives you meaningful logs without the performance penalty and maintenance overhead of excessive logging!

---

Great question 👌 You’re basically asking:

👉 *“If I pass data through several layers of functions, where should I log? Only in the final function, or in each layer?”*

---

## 🔹 How logging works

Logging does **not depend** on parameter passing.
It only depends on **where you call `logger.info(...)`** in your code.

Example:

```python
import logging
logger = logging.getLogger("my_app")

def func_a(x):
    logger.debug("func_a called")
    return func_b(x)

def func_b(y):
    logger.debug("func_b called")
    return func_c(y)

def func_c(z):
    logger.debug("func_c called")
    return z * 2

print(func_a(5))
```

### Output

```
my_app - DEBUG - func_a called
my_app - DEBUG - func_b called
my_app - DEBUG - func_c called
```

👉 Logging happens **wherever you place it**, not automatically at the final function.

---

## 🔹 Best practice: Where should you log?

You don’t want to **spam logs everywhere**, but also don’t want to **lose context**.
Here’s a good strategy:

1. **Top-level function (entry point)**

   * Log **intent**: what you’re trying to do.
   * Example:

     ```python
     logger.info("Creating note for user %s", user_id)
     ```

2. **Intermediate functions (business logic)**

   * Log **important decisions, branching, or unusual behavior**.
   * Example:

     ```python
     if not notebook:
         logger.warning("Notebook %s not found for user %s", nb_id, user_id)
     ```

3. **Final / low-level function (DB, external API, worker)**

   * Log **results or errors** (success/failure).
   * Example:

     ```python
     logger.debug("Executing SQL: INSERT INTO notes ...")
     logger.info("Note %s saved successfully", note.id)
     ```

---

## 🔹 Example in your Smart Notes project

```python
def create_note_api(note_data, user_id):
    logger.info("API request to create note for user %s", user_id)
    return save_note_service(note_data, user_id)

def save_note_service(note_data, user_id):
    logger.debug("Validating note data for user %s", user_id)
    return note_repository.save(note_data, user_id)

def save(note_data, user_id):
    logger.debug("Inserting note into DB for user %s", user_id)
    # ... insert into Postgres
    logger.info("Note saved successfully for user %s", user_id)
```

### Logs:

```
INFO  API request to create note for user 42
DEBUG Validating note data for user 42
DEBUG Inserting note into DB for user 42
INFO  Note saved successfully for user 42
```

---

## 🔎 Best scenario

* **Don’t log the same thing in every layer** → causes duplication & noise.
* **Top layer**: what was asked.
* **Middle layers**: decisions & warnings.
* **Final layer**: actual result or failure.

That way, when you trace logs, you see a **story**:
Request came in → validated → DB insert → success/failure.

---

⚡ In short:
➡️ Logging should be **distributed across layers**, but each layer logs **different kinds of info** (not the same message repeated).

---

👉 Do you want me to draft a **logging strategy guide** for your whole project (API, services, repositories, workers, AI clients) so your logs are consistent and not noisy?
