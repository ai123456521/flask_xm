# @ Time    : 2020/11/25 21:22


from celery import Celery

celery_app = Celery("home")

# 加载配置文件
celery_app.config_from_object("lghome.tasks.config")

# 注册任务
celery_app.autodiscover_tasks(["lghome.tasks.sms"])

# celery 启动
# celery -A lghome.tasks.main worker -l info -P eventlet

