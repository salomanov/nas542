import urllib.request
import ssl
import base64

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Test upload into root
url = 'https://178.140.8.56:34501/pkg/ownCloud/remote.php/dav/files/admin/test_root_upload.txt'
req = urllib.request.Request(url, data=b'TEST_UPLOAD_CONTENT', headers={'Content-Type': 'application/octet-stream'})
req.add_header('Authorization', 'Basic ' + base64.b64encode(b'admin:12345678').decode())
req.get_method = lambda: 'PUT'

try:
    with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
        print("ROOT UPLOAD STATUS:", r.getcode())
except Exception as e:
    print("ROOT UPLOAD ERR:", e)

# 2. Test upload into Личное
url2 = 'https://178.140.8.56:34501/pkg/ownCloud/remote.php/dav/files/admin/%D0%9B%D0%B8%D1%87%D0%BD%D0%BE%D0%B5/test_folder_upload.txt'
req2 = urllib.request.Request(url2, data=b'TEST_UPLOAD_CONTENT_IN_FOLDER', headers={'Content-Type': 'application/octet-stream'})
req2.add_header('Authorization', 'Basic ' + base64.b64encode(b'admin:12345678').decode())
req2.get_method = lambda: 'PUT'

try:
    with urllib.request.urlopen(req2, context=ctx, timeout=5) as r:
        print("FOLDER UPLOAD STATUS:", r.getcode())
except Exception as e:
    print("FOLDER UPLOAD ERR:", e)

# Clean up test files
for u in [url, url2]:
    try:
        del_req = urllib.request.Request(u)
        del_req.add_header('Authorization', 'Basic ' + base64.b64encode(b'admin:12345678').decode())
        del_req.get_method = lambda: 'DELETE'
        urllib.request.urlopen(del_req, context=ctx, timeout=5)
    except:
        pass
