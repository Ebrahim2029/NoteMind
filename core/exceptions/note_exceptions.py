class NoteException(Exception):
    """الاستثناء الأساسي لجميع الأخطاء المتعلقة بالملاحظات.
    
    جميع استثناءات الملاحظات الأخرى ترث من هذا الكلاس.
    """
    pass

class InvalidNoteAttributeException(NoteException):
    """يتم رفعه عندما يكون هناك خطأ في إحدى خصائص الملاحظة، مثل نوع غير صحيح أو قيمة غير صالحة."""
    pass

class NoteNotFoundException(NoteException):
    """يتم رفعه عندما لا يتم العثور على الملاحظة المطلوبة."""
    pass

class NoteUpdateException(NoteException):
    """يتم رفعه عند حدوث خطأ أثناء تعديل الملاحظة."""
    pass

class NoteDeleteException(NoteException):
    """يتم رفعه عند حدوث خطأ أثناء حذف الملاحظة."""
    pass
