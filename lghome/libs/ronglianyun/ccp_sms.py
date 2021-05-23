# @ Time    : 2020/11/20 22:03


from ronglian_sms_sdk import SmsSDK
import json

accId = '8aaf0708762cb1cf01763c7f30950548'
accToken = '63bc2f08198440569addc55fe68c63da'
appId = '8aaf0708762cb1cf01763c7f3194054f'


class CCP(object):
    """发送短信的单例类"""
    # _instance = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.sdk = SmsSDK(accId, accToken, appId)
        return cls._instance

    def send_message(self, mobile, datas, tid):
        sdk = self._instance.sdk
        # sdk = self.sdk
        # tid = '1'
        # mobile = '15702902893'
        # datas  验证码   过期时间 单位是分钟
        # datas = ('1234', '5')
        resp = sdk.sendMessage(tid, mobile, datas)
        result = json.loads(resp)
        if result['statusCode'] == '000000':
            return 0
        else:
            return -1


if __name__ == '__main__':
    # send_message()
    c = CCP()
    c.send_message('15702902893', ('1234', '5'), 1)

