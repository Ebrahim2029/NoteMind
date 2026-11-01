class NotebookException(Exception):
    """الاستثناء الأساسي لجميع الأخطاء المتعلقة بدفاتر الملاحظات.
    
    جميع استثناءات دفتر الملاحظات الأخرى ترث من هذا الكلاس.
    """
    pass

class InvalidNotebookAttributeException(NotebookException):
    """يتم رفعه عندما يكون هناك خطأ في إحدى خصائص دفتر الملاحظات، مثل نوع غير صحيح أو قيمة غير صالحة."""
    pass

class NotebookNotFoundException(NotebookException):
    """يتم رفعه عندما لا يتم العثور على دفتر الملاحظات المطلوب."""
    pass

class NoteNotInNotebookException(NotebookException):
    """يتم رفعه عندما تحاول التعامل مع ملاحظة غير موجودة داخل دفتر الملاحظات."""
    pass

class NotebookUpdateException(NotebookException):
    """يتم رفعه عند حدوث خطأ أثناء تعديل دفتر الملاحظات."""
    pass

class NotebookDeleteException(NotebookException):
    """يتم رفعه عند حدوث خطأ أثناء حذف دفتر الملاحظات."""
    pass
