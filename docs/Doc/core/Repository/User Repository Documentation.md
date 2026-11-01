<div dir="rtl">

---



# User Repository Documentation

## Overview

`UserRepository` هو طبقة **Repository Pattern** مسؤولة عن إدارة عمليات الوصول والتعديل على بيانات المستخدمين في قاعدة البيانات، مع دعم **Redis Read-Through Cache** لزيادة الأداء.
يوفر واجهة موحدة بين الطبقة الدومينية (Domain Entities) وطبقة التخزين (PostgreSQL + Redis).

---

## Responsibilities

* تنفيذ عمليات **CRUD** (إنشاء، قراءة، تحديث، حذف) على بيانات المستخدمين.
* إدارة الكاش باستخدام **Redis** مع سياسة **auto-refresh TTL**.
* توفير عمليات تصفية متقدمة للمستخدمين.
* التعامل مع الأخطاء الخاصة بالمستخدمين عبر Exceptions مخصصة.

---

## Dependencies

* **PostgreSQL** (تخزين البيانات الأساسية)
* **Redis** (تخزين مؤقت Read-Through)
* **SQLAlchemy ORM** (إدارة الاستعلامات)
* **Domain Entities**:

  * `User` من `core.entities.user`
* **Custom Exceptions**:

  * `UserNotFoundException`
  * `DuplicateUserException`
  * `UserUpdateException`
* **Cache Utilities** من `infrastructure.cache`

---

## Class: `UserRepository`

### **Constructor**

```python
def __init__(self, db_session: Session, cache_ttl: int = DEFAULT_TTL_SECONDS)
```

* **db\_session**: جلسة SQLAlchemy لإدارة العمليات على قاعدة البيانات.
* **cache\_ttl**: عمر البيانات في الكاش بالثواني (افتراضي 15 دقيقة).

---

### **Methods**

#### 1. `get_by_id(user_id: UUID) -> User`

* **الوصف**: جلب بيانات مستخدم عبر المعرف `UUID` مع دعم الكاش.
* **الكاش**: قراءة من Redis، وإذا لم يوجد يتم الجلب من PostgreSQL وتخزين النتيجة.
* **الأخطاء**: يرفع `UserNotFoundException` إذا لم يتم العثور على المستخدم.

---

#### 2. `get_by_email(email: str) -> User`

* **الوصف**: جلب مستخدم عبر البريد الإلكتروني.
* **الكاش**: مشابه لـ `get_by_id` مع تخزين النتيجة في مفاتيح `USER_BY_EMAIL` و `USER_BY_ID`.

---

#### 3. `filter_users(...) -> List[User]`

* **الوصف**: تصفية المستخدمين بناءً على معايير مثل:

  * الاسم يحتوي على نص
  * البريد يحتوي على نص
  * الحالة (نشط/غير نشط)
  * التاريخ (من / إلى)
* **الفرز**: يدعم `created_at` و `username` تصاعدياً أو تنازلياً.
* **الإرجاع**: قائمة كائنات `User`.

---

#### 4. `create(user: User) -> User`

* **الوصف**: إنشاء مستخدم جديد وتخزينه في PostgreSQL وتحديث الكاش.
* **الأخطاء**:

  * `DuplicateUserException` إذا كان البريد أو اسم المستخدم موجوداً.

---

#### 5. `update(user: User) -> User`

* **الوصف**: تحديث بيانات مستخدم موجود مع تحديث الكاش.
* **الأخطاء**:

  * `UserNotFoundException` إذا لم يوجد المستخدم.
  * `UserUpdateException` لأي خطأ في عملية التحديث.

---

#### 6. `delete(user_id: UUID) -> None`

* **الوصف**: تعطيل (Soft Delete) مستخدم عبر جعل `is_active=False` وحذف الكاش.
* **الأخطاء**:

  * `UserNotFoundException` إذا لم يوجد المستخدم.

---

## Caching Strategy

* **Keys**:

  * `user:{user_id}`
  * `user:email:{email}`
* **Policy**: Read-Through + TTL Auto-Refresh.
* **Invalidation**: عند التحديث أو الحذف.

---

## Example Usage

```python
from core.repositories.user_repository import UserRepository
from core.entities.user import User
from infrastructure.database import SessionLocal

db = SessionLocal()
repo = UserRepository(db)

# إنشاء مستخدم جديد
new_user = User(username="john_doe", email="john@example.com")
created = repo.create(new_user)

# جلب المستخدم من الكاش أو قاعدة البيانات
user = repo.get_by_id(created.id.value)

# تحديث البريد الإلكتروني
user.update_email("new_email@example.com")
repo.update(user)

# تعطيل المستخدم
repo.delete(user.id.value)
```

---

## Error Handling

* يلتزم `UserRepository` برفع Exceptions مخصصة بدلاً من الأخطاء العامة لسهولة المعالجة في الـ API.

---

📄 **ملاحظات**

* ينصح بتفعيل **pgcrypto** في PostgreSQL لدعم `gen_random_uuid()`.
* Redis يجب أن يكون قيد التشغيل قبل استخدام هذه الوحدة.

---

