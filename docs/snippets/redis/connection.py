""" import redis

# إنشاء اتصال بـ Redis (الافتراضي: localhost, port=6379)
r = redis.Redis(host='localhost', port=6379, db=0)

# اختبار الاتصال
response = r.ping()
print(f"Connected to Redis! {response}" if response else "Failed to connect!")
print(type(r))
 """

import redis

# إنشاء مجمع اتصالات
pool = redis.ConnectionPool(host='localhost', port=6379, db=0, max_connections=10)
r = redis.Redis(connection_pool=pool)


# اختبار الاتصال
if r.ping():
        # تخزين واسترجاع بيانات
    r.set("user:2", "Ebrahem")  # تخزين قيمة
    name = [r.get(f"user:{i}").decode('utf-8') for i in range(1, 3)]  # استرجاع القيمة
    print(name)  # الناتج: ["Ahmed", "Ebrahem"]

    # زيادة/نقصان قيمة رقمية
    r.set("counter", 0)
    r.incr("counter")  # تصبح 1
    print(r.get("counter").decode('utf-8'))  # الناتج: "1"
    #r.decr("counter")  # تصبح 0
else:
    print("Connection failed!")

# الحصول على إحصائيات الأداء
info = r.info()
print(f"connected_clients: {info['connected_clients']}")
print(f"used_memory_human: {info['used_memory_human']}")
print(f"instantaneous_ops_per_sec: {info['instantaneous_ops_per_sec']}")

# تحليل بطء الأوامر

""" slow_log = r.slowlog_get(5)
for entry in slow_log:
    print(f"duration: {entry['duration']}ms", 
          f"command: {entry['command'].decode('utf-8')}")
 """