import httplib2

img_url = 'http://ptimg.org:88/dapenti/G0vppcb1/utiFM.jpg'
target_filename = 'UtiFm.jpg'
timeout = 10  # second
h = httplib2.Http(".cache", timeout=timeout)
try:
    resp, content = h.request(img_url, "GET")
    with open(target_filename, 'wb') as f:
        f.write(content)
except Exception as e:
    print(e)