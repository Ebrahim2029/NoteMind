<div dir="rtl">

---

# Notebook Repository Documentation

## نظرة عامة

`NotebookRepository` يطبّق **Repository Pattern** لإدارة دفاتر الملاحظات (Notebooks) عبر PostgreSQL مع تكامل **Redis read‑through cache** لزيادة سرعة جلب الدفاتر بالمعرّف. يُقدّم عمليات CRUD، فلاتر مرنة، وجلب دفاتر مستخدم معيّن.

---

## المسؤوليات

* CRUD لدفاتر الملاحظات مع تحديث/إبطال الكاش بعد عمليات الكتابة.
* جلب دفتر بالـ `UUID` باستخدام كاش القراءة (read‑through).
* جلب دفاتر مستخدم محدّد وترتيبها زمنياً.
* تصفية الدفاتر بالاسم/اللون مع خيارات ترتيب.

---

## الاعتمادات (Dependencies)

* **SQLAlchemy ORM**: جلسة DB ونموذج `NotebookModel`.
* **Domain Entity**: الكيان `Notebook`.
* **Redis Cache Utils**: مفاتيح الكاش وعمليات `get_hash/set_hash/refresh_ttl/del_key`.
* **Exceptions**: `NotebookNotFoundException`, `NotebookUpdateException`.

---

## بنية البيانات المختصرة

* **ORM** `notebooks`: الحقول `id`, `user_id`, `name`, `color` + الحقول المشتركة (`created_at`, `updated_at`) وعلاقات مع `users` و`notes`.
* **Entity**: كيان `Notebook` يحوي خصائص الاسم، اللون، مجموعة الملاحظات… مع تحقق الدومين.

---

## الكلاس: `NotebookRepository`

### المُنشئ

```python
def __init__(self, db_session: Session, cache_ttl: int = DEFAULT_TTL_SECONDS)
```

* `db_session`: جلسة SQLAlchemy.
* `cache_ttl`: TTL افتراضي للكاش (ثواني).

---

### واجهة الاستخدام (Public API)

#### 1) `get_by_id(notebook_id: UUID) -> Notebook`

* **الوصف**: يحاول الجلب من Redis أولاً، وإن لم يجد، يجلب من PostgreSQL، ثم يخزّن النتيجة ويعمل **auto‑refresh TTL** عند القراءة.
* **الأخطاء**: `NotebookNotFoundException` عند عدم الوجود.

#### 2) `get_by_user(user_id: UUID) -> List[Notebook]`

* **الوصف**: يعيد دفاتر مستخدم معيّن مرتّبة تنازلياً حسب `created_at`.

#### 3) `filter_notebooks(user_id: Optional[UUID], name_contains: Optional[str], color_in: Optional[List[str]], order_by: str = "created_at desc", limit: int = 100, offset: int = 0) -> List[Notebook]`

* **الوصف**: فلترة مرنة حسب المالك، جزء من الاسم، قائمة ألوان؛ وترتيب حسب `name asc/desc` أو `created_at desc`.

#### 4) `create(notebook: Notebook) -> Notebook`

* **الوصف**: ينشئ دفترًا جديدًا، يثبّت المعاملة، ثم يحدّث الكاش بمفتاح `notebook:{notebook_id}`.
* **الأخطاء**: `NotebookUpdateException` عند فشل الكتابة.

#### 5) `update(notebook: Notebook) -> Notebook`

* **الوصف**: يحدّث الاسم/اللون، ثم ينعش كيان الكاش بنفس المفتاح.
* **الأخطاء**: `NotebookNotFoundException` أو `NotebookUpdateException`.

#### 6) `delete(notebook_id: UUID) -> None`

* **الوصف**: يحذف الدفتر من PostgreSQL ويُبطل مفتاح الكاش المرتبط.

---

## استراتيجية الكاش

* **المفتاح**: `notebook:{notebook_id}` (راجع `CacheKeys`).
* **Read‑Through**: قراءة من Redis → إن لم يوجد من DB → تخزين في Redis.
* **Auto‑Refresh TTL**: عند نجاح القراءة من الكاش.
* **Invalidation**: على `update`/`delete` يتم تحديث/حذف المفتاح.

---

## أمثلة استخدام

```python
from uuid import UUID
from infrastructure.database import SessionLocal
from core.repositories.notebook_repository import NotebookRepository
from core.entities.notebook import Notebook

db = SessionLocal()
repo = NotebookRepository(db)

# إنشاء دفتر
nb = Notebook(user_id=UUID("..."), name="Research", color="#E3F2FD")
created = repo.create(nb)

# جلب بالمعرّف (من الكاش/DB)
fetched = repo.get_by_id(created.id.value)

# جلب دفاتر مستخدم
user_books = repo.get_by_user(created.user_id)

# فلترة بالاسم واللون
filtered = repo.filter_notebooks(
    user_id=created.user_id,
    name_contains="Res",
    color_in=["#E3F2FD"],
    order_by="name asc",
    limit=20
)

# تحديث
fetched.rename("Research 2025")
fetched.change_color("#BBDEFB")
updated = repo.update(fetched)

# حذف
repo.delete(updated.id.value)
```

---

## اعتبارات التصميم والاختبارات

* **الفهارس**: يوصى بفهرس على `user_id` وفهرس على `created_at` لتحسين الاستعلامات الشائعة. *(توصية تنفيذية)*
* **اتساق الكاش**: تحديث الكاش يتم **بعد** نجاح `commit` لتجنّب الاتساق المؤقت.
* **اختبارات مقترحة (pytest)**:

  * read‑through: أول قراءة من DB، والثانية من الكاش.
  * filter\_notebooks: تصفية بالاسم/اللون مع الترتيب والتقسيم `limit/offset`.
  * إبطال الكاش عند `update/delete`.
  * رفع الاستثناءات الصحيحة عند عدم الوجود.

---

## ملاحظات تكامل

* توحيد سياسة الألوان والأسماء مع قواعد الدومين في `Notebook` (التحقق والقيود) لضمان صحة البيانات من الطبقتين.
* ربط عمليات الحذف مع حذف/أرشفة الملاحظات التابعة حسب سياسة العمل (حذف فعلي vs. منطقي). *(يعتمد على متطلبات المنتج)*

---

