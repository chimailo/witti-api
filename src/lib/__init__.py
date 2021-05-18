import base64

def urlsafe_base64(value, from_base64=False, encoding='utf-8'):
    to_bytes = bytes(value, encoding)
    to_base64 = b''

    if from_base64:
        to_base64 = base64.urlsafe_b64decode(to_bytes)
    else:
        to_base64 = base64.urlsafe_b64encode(to_bytes)

    return bytes.decode(to_base64, encoding)
