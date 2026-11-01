class UserException(Exception):
    """الاستثناء الأساسي لجميع الأخطاء المتعلقة بالمستخدمين.
    
    جميع استثناءات المستخدم الأخرى ترث من هذا الكلاس.
    """
    pass

class InvalidUserAttributeException(UserException):
    """يتم رفعه عندما تكون إحدى خصائص المستخدم غير صالحة أو خاطئة."""
    pass

class UserNotFoundException(UserException):
    """يتم رفعه عندما لا يتم العثور على المستخدم المطلوب."""
    pass

class DuplicateUserException(UserException):
    """يتم رفعه عند محاولة إنشاء مستخدم بنفس اسم المستخدم أو البريد الإلكتروني الموجود مسبقًا."""
    pass

class UserUpdateException(UserException):
    """يتم رفعه عند حدوث خطأ أثناء تعديل بيانات المستخدم."""
    pass

class UserDeleteException(UserException):
    """يتم رفعه عند حدوث خطأ أثناء حذف المستخدم."""
    pass
