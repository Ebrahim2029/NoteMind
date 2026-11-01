<div dir="rtl">

---

# Note Repository Documentation

## نظرة عامة

`NoteRepository` يطبّق **Repository Pattern** لطبقة الملاحظات، ويوحّد الوصول بين الدومين (`Note`) وطبقة التخزين (PostgreSQL) مع **Redis read‑through cache** لجلب الملاحظة بالمعرّف بسرعة. كما يوفّر فلاتر مرنة، وبحث نصي بسيط، وتصفية بالوسوم باستخدام معاملات مصفوفات PostgreSQL.

---

## المسؤوليات

* عمليات CRUD للملاحظات مع تحديث/إبطال الكاش بعد الكتابة.
* جلب ملاحظة بالـ `UUID` عبر كاش القراءة (read‑through).
* ترشيح ملاحظات بدفتر محدّد أو وفق وسوم/حالات/مدى زمني/نص.
* ترتيب مرشّحات البحث بوزنية تجمع التشابه الدلالي والحداثة وآخر وصول (واجهة تحضيرية للتكامل مع الذكاء الاصطناعي).

---

## الاعتمادات (Dependencies)

* **SQLAlchemy ORM** (جلسة قاعدة البيانات، نماذج ORM: `NoteModel`).
* **Domain Entity**: `Note` (الكيان الدوميني).
* **Redis Cache Utils**: مفاتيح الكاش وعمليات `get_hash/set_hash/refresh_ttl/del_key`.
* **Exceptions**: `NoteNotFoundException`, `NoteUpdateException`.
* **Scoring Utils**: `compute_weighted_score` لحساب Score مركّب.

---

## بنية البيانات المختصرة

* **ORM**: جدول `notes` يتضمن الحقول: `id`, `notebook_id`, `title`, `content`, `tags` (ARRAY), حالات مثل `is_pinned/is_archived/is_deleted`, `reminder`, `attachments`, وحقول التوقيت.
* **Entity**: كيان `Note` يعكس سلوك/تحقّق الدومين (عناوين، محتوى، وسوم، حالات...).

---

## الكلاس: `NoteRepository`

### المُنشئ

```python
def __init__(self, db_session: Session, cache_ttl: int = DEFAULT_TTL_SECONDS)
```

* `db_session`: جلسة SQLAlchemy.
* `cache_ttl`: TTL افتراضي للكاش (ثواني).

---

### واجهة الاستخدام (Public API)

#### 1) `get_by_id(note_id: UUID) -> Note`

* **الوصف**: يجلب الملاحظة عبر الكاش (إن وُجد)، وإلا من PostgreSQL ثم يضعها في الكاش مع **auto‑refresh TTL** عند القراءة.
* **الأخطاء**: `NoteNotFoundException` إن لم توجد الملاحظة.

#### 2) `get_by_notebook(notebook_id: UUID, include_deleted: bool = False) -> List[Note]`

* **الوصف**: يعيد ملاحظات دفتر محدّد، بترتيب تنازلي حسب تاريخ الإنشاء؛ يمكن إخفاء المحذوفة منطقياً.

#### 3) `filter_notes(..., tags_any: List[str] | None, tags_all: List[str] | None, text_query: str | None, order_by: str = "created_at desc") -> List[Note]`

* **الوصف**: فلترة مرنة حسب: الدفتر، الوسوم (تقاطع `&&` لأي من الوسوم، أو احتواء `@>` لكل الوسوم)، الحالات، النطاق الزمني، أو نص في `title/content`.
* **ملاحظة**: يعتمد معاملات مصفوفات Postgres: `tags && [:]` للتقاطع و`tags @> [:]` للاحتواء.
* **الفرز**: `created_at desc` افتراضيًا، ويدعم `updated_at desc` و`title asc`.

#### 4) `rank_notes_for_query(candidates: List[Note], semantic_scores: List[float]) -> List[tuple[Note, float]]`

* **الوصف**: يحسب درجة مركّبة (تحضيريًا للبحث الدلالي):

  * `0.7 * semantic_similarity + 0.2 * recency + 0.1 * last_accessed` (قيم الوقت حالياً افتراضية لحين توفّرها).

#### 5) `create(note: Note) -> Note`

* **الوصف**: ينشئ ملاحظة جديدة ويحدّث الكاش (`note:{note_id}`).
* **الأخطاء**: `NoteUpdateException` عند فشل الكتابة.

#### 6) `update(note: Note) -> Note`

* **الوصف**: يحدّث الملاحظة ويعيد تهيئة الكاش بالمحتوى الجديد.
* **الأخطاء**: `NoteNotFoundException` إذا لم توجد؛ وإلا `NoteUpdateException`.

#### 7) `delete(note_id: UUID) -> None`

* **الوصف**: حذف منطقي (تعيين `is_deleted=True`) ثم **حذف مفتاح الكاش**.

---

## استراتيجية الكاش

* **المفاتيح**: `note:{note_id}` (انظر تعريف المفاتيح في `CacheKeys`).
* **Read‑Through**: القراءة من Redis أولاً، ثم من DB، ثم حفظ النتيجة.
* **Auto‑Refresh**: عند القراءة من الكاش يتم تحديث TTL.
* **Invalidation**: بعد `update` أو `delete` يتم حذف/تحديث المفتاح.

---

## أمثلة استخدام

```python
from uuid import UUID
from core.repositories.note_repository import NoteRepository
from core.entities.note import Note
from infrastructure.database import SessionLocal

db = SessionLocal()
repo = NoteRepository(db)

# إنشاء
note = Note(title="Daily Log", content="Standup notes", tags=["work", "daily"])
created = repo.create(note)

# جلب عبر الكاش/DB
fetched = repo.get_by_id(created.id.value)

# فلترة بالوسوم والنص
filtered = repo.filter_notes(tags_any=["work"], text_query="Standup", order_by="updated_at desc")

# بدفتر محدد وإخفاء المحذوف
notes_in_book = repo.get_by_notebook(UUID("..."), include_deleted=False)

# تحديث
fetched.update_content("Updated content")
updated = repo.update(fetched)

# حذف منطقي
repo.delete(updated.id.value)
```

---

## اعتبارات التصميم والاختبارات

* **الأداء**: استخدم فهارس Postgres على الأعمدة `notebook_id`, `created_at`, وGIN على `tags` لتحسين معاملات `&&` و`@>`. *(توصية تنفيذية)*
* **الاتساق**: تحديث الكاش يتم فقط **بعد نجاح** الـ commit.
* **اختبارات مقترحة (pytest)**:

  * جلب عبر الكاش بعد أول قراءة من DB.
  * فلترة بالوسوم: `tags_any` مقابل `tags_all`.
  * إبطال الكاش عند `update/delete`.
  * ترتيب النتائج وفق `order_by`.
  * رفع الاستثناءات الصحيحة عند عدم الوجود.

---

## ملاحظات تكامل مستقبلية

* ربط `rank_notes_for_query` بناتج استعلام دلالي من **ChromaDB** ثم تمرير `semantic_scores` الفعلية.
* نقل أزمنة `created_at/updated_at` إلى الكيان أو إحضارها عند الترتيب لتحسين مركّب الحداثة/آخر وصول.

---

