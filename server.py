import socket
import urllib.parse
import random

ENTRIES = ['Pavel was here']

SESSIONS = {}

def handle_connection(conx):
    # the request line
    req = conx.makefile("b")
    reqline = req.readline().decode('utf8')
    method, url, version = reqline.split(" ", 2)
    assert method in ["GET", "POST"]
    
    headers = {}
    while True:
        line = req.readline().decode('utf8')
        if line == '\r\n': break
        header, value = line.split(":", 1)
        headers[header.casefold()] = value.strip()
        
    if 'content-length' in headers:
        length = int(headers['content-length'])
        body = req.read(length).decode('utf8')
    else:
        body = None
        
    # generate or obtain token cookie from browser
    if "cookie" in headers:
        token = headers["cookie"][len("token="):]
    else:
        token = str(random.random())[2:]
    
    session = SESSIONS.setdefault(token, {})
    status, body = do_request(session, method, url, headers, body)
    
    print("do_request:\n")
    print(status)
    print(body)
    print("\n")
    
    response = "HTTP/1.0 {}\r\n".format(status)
    response += "Content-Length: {}\r\n".format(
        len(body.encode('utf8'))
    )
    
    # new visitors need to remember their newly generated token
    if "cookie" not in headers:
        template = "Set-Cookie: token={}\r\n"
        response += template.format(token)
    
    response += "\r\n" + body
    conx.send(response.encode('utf8'))
    conx.close()
    
def form_decode(body):
    params = {}
    for field in body.split("&"):
        name, value = field.split("=", 1)
        name = urllib.parse.unquote_plus(name)
        value = urllib.parse.unquote_plus(value)
        params[name] = value
    return params

def add_entry(session, params):
    print("params:")
    print(params)
    print("\n")
    if 'guest' in params:
        ENTRIES.append(params['guest'])
    print("Entries:")
    print(ENTRIES)
    print("\n")
    return show_comments()

def not_found(url, method):
    out = "<!doctype html>"
    out += "<h1>{} {} not found</h1>".format(method, url)
    return out
    
# the session data gets passed to individual pages like show_comments, add_entry
def do_request(session, method, url, headers, body):
    if method == "GET" and url == "/":
        return "200 OK", show_comments(session)
    elif method == "POST" and url == "/add":
        params = form_decode(body)
        add_entry(session, params)
        return "200 OK", show_comments(session)
    elif method == "GET" and url == "/comment.js":
        with open("comment.js") as f:
            return "200 OK", f.read()
    elif method == "GET" and url == "/comment.css":
        with open("comment.css") as f:
            return "200 OK", f.read()
    else:
        return "404 Not Found"    

def show_comments(session):
    out = "<!doctype html>"
    out += "<script src=/comment.js></script>"
    out += "<link rel='stylesheet' href=/comment.css>"
    out += "<form action=add method=post>"
    out += "<p><input name=guest></p>"
    out += "<p><button>Sign the book!</button></p>"
    out += "</form>"
    out += "<strong></strong>"
    print("Entries to be inserted in HTML:")
    for entry in ENTRIES:
        print(entry)
        out += "<p>" + entry + "</p>"
    print("\n")
    return out

s = socket.socket(
    family = socket.AF_INET,
    type = socket.SOCK_STREAM,
    proto = socket.IPPROTO_TCP
)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

""" instead of calling connect to connect to a server we call bind which waits 
for a computer to connect - the first argument specifies who can connect: it
being empty means anyone can - the second argument is the port others must use
to talk to our server: ports below 1024 require administrative priviledges, so
8000 was arbitraily chosen """
s.bind(('', 8000))
# the listen call tells the OS that we're ready to accept connections
s.listen()

# to accept those connections, we enter a loop that runs once per connection
while True:
    conx, addr = s.accept()
    handle_connection(conx)
    
