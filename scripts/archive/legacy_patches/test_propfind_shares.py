import urllib.request, ssl, sys

ctx = ssl._create_unverified_context()
body = """<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop><oc:id/><oc:permissions/><oc:share-types/></d:prop></d:propfind>"""
req = urllib.request.Request('https://178.140.8.56:34501/pkg/ownCloud/remote.php/dav/files/admin/%D0%9B%D0%B8%D1%87%D0%BD%D0%BE%D0%B5/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D1%89%D0%B8%D0%BA%D0%B8/%D0%90%D0%BD%D0%B4%D1%80%D0%BE%D0%B8%D0%B4/',
    data=body.encode(), method='PROPFIND',
    headers={'Authorization': 'Basic YWRtaW46MTIzNDU2Nzg=', 'Depth': '1', 'Content-Type': 'application/xml'})
try:
    r = urllib.request.urlopen(req, context=ctx)
    print(r.status)
    sys.stdout.buffer.write(r.read()[:2500])
except Exception as e:
    print('ERR', e)
    try:
        sys.stdout.buffer.write(e.read()[:800])
    except Exception:
        pass
