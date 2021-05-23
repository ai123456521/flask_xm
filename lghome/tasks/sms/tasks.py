# @ Time    : 2020/11/25 21:21


from lghome.tasks.main import celery_app
from lghome.libs.ronglianyun.ccp_sms import CCP


@celery_app.task
def send_sms(mobile, datas, tid):
    """发送短信的异步任务"""
    ccp = CCP()
    ccp.send_message(mobile, datas, tid)