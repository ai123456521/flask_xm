# @ Time    : 2020/11/27 21:37
from qiniu import Auth, put_file, etag, put_data

# 需要填写你的 Access Key 和 Secret Key
access_key = 'AA-RuvuYlaSATaQIWUs_rClYew7SgU-tYDAK__5A'
secret_key = 'AyYKiVNY2SQATR_g5zig052JEbIA3X0JqLHauHad'


def storage(file_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    # bucket_name = 'images-flask'
    bucket_name = 'im-flask'
    # 上传后保存的文件名
    # key = 'my-python-logo.png'
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    ret, info = put_data(token, None, file_data)
    if info.status_code == 200:
        return ret.get('key')
    else:
        raise Exception('上传图片失败')
    # print(ret)
    # print("-"*50)
    # print(info)


if __name__ == '__main__':
    with open("target.txt", 'rb') as f:
        storage(f.read())
