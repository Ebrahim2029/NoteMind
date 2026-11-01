from core.repositories.models.note_models import NoteModel
from core.repositories.models.user_models import UserModel
from core.repositories.models.notebook_models import NotebookModel
from infrastructure.database import SessionLocal
from utils.fake_data import generate_fake_data

# توليد بيانات عشوائية
data = generate_fake_data()

print(f"\nName: {data['name']}")
print(f"Email: {data['email']}")
print(f"Note: {data['note']}")
print(f"Notebook: {data['notebook']}\n")


# ✅ Example 1: إنشاء مستخدم مع دفتر ملاحظات وملاحظة
with SessionLocal() as session:
    user = UserModel(username=data["name"], email=data["email"])
    notebook = NotebookModel(name=data["notebook"], user=user)   # ربط مباشر
    note = NoteModel(title=data["note"], notebook=notebook)   # ربط مباشر

    session.add(user)  # إضافة المستخدم تكفي، لأنه يحتوي على كل العلاقات
    session.commit()

# ✅ Example 2: جلب جميع الملاحظات لمستخدم معيّن
with SessionLocal() as session:
    user = session.query(UserModel).first()
    for notebook in user.notebooks:      # علاقة One-to-Many
        for note in notebook.notes:      # علاقة One-to-Many أخرى
            print(note.title)

# ✅ Example 3: جلب دفتر الملاحظات المرتبط بملاحظة
with SessionLocal() as session:
    note = session.query(NoteModel).first()
    print(note.notebook.name)  # التحميل التلقائي

""" # ✅ Example 4: الحذف مع الكاسكيد
with SessionLocal() as session:
    user = session.query(UserModel).first()
    if user:
        session.delete(user)  # إذا كان cascade مضبوط، سيحذف كل شيء مرتبط
        session.commit()
 """