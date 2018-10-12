#!python3
# import necessary libraries
import os
import sys
import asyncio
import time
import platform
import mimetypes  # to classify the file type, e.g. text, image...
from copy import copy


# record the visited url
last_visited = None


# handle the request using asyncio
async def request_handler(reader, writer):
    while True:  # loop to wait and handle requests
        raw_request = await reader.read(2048)  # reading the stream
        request = raw_request.decode('utf-8')  # decode bytes string to normal string
        if not raw_request:
            break
        else:
            req_dict = resolve_request(request)  # resolve the request string
            method = req_dict["method"]
            file = req_dict["file"]
            ranges = req_dict["range"]
            host = req_dict["host"]
            # version = req_dict["version"]
            # if version != "HTTP/1.0":  # do not support HTTP/1.1 request
                # response = error_handler(505)
            if method == "POST":  # for POST
                response = post_handler() 
            elif method == "GET":  # for GET
                response = get_handler(file, has_range=ranges, host=host)
                print(last_visited)
            elif method == "HEAD":  # for HEAD
                response = head_handler(file)
            else:  # others, regard as an error
                response = error_handler(400)
            print(response)  # for debug, print the request received
            data = response.encode()  # encode the data
            writer.write(data)  # write data to writer stream
            await writer.drain()
        writer.close()


# resolve the request received
def resolve_request(request_text):
    req_dict = {}  # kyewords: method, file, range, version 
    req_list = request_text.split("\r\n")
    print(req_list)  # for debug
    req_info = req_list[0].split(" ")  # first string, assume to be the protocol, e.g. GET ... or HEAD ...
    method = req_info[0]  # GET, HEAD or POST
    file = "." + req_info[1]  # add "." to the file path, like "." + "/" = "./" 
    version = req_info[2]  # HTTP/1.0 or HTTP/1.1 
    ranges = []  # record the bytes range for partial content GET
    host = ""
    for line in req_list:
        line_split = line.split(":")
        if line_split[0] == "Range":  # the format is like: Range: bytes=0-9,12-16
            # take "Range: bytes=0-9,12-16" for an example, line_split[1]: "bytes=0-9,12-16", split by "="
            # we get "bytes" and "0-9,12-16", [1] to access "0-9,12-16"
            # "0-9,12-16" is split by "," --> "0-9" and "12-16"
            range_list = line_split[1].split("=")[1].split(",")  
            # ranges is a list, the elements in it is tuple. As we split the string in previous step, we finally 
            # format the string to be integer numbers in tuple, like [(0, 9), (12, 16)] ... [(begin, end),...]
            # int(v) convert string to integer
            # [int(v) for v in r.split("-")] firstly split the string to "0", "9" then use int(v) to get 0 and 9
            # [... for r in range_list]: range_list contains all substrings like "0-9", "12-16"
            ranges = [tuple([int(v) for v in r.split("-")]) for r in range_list]
        elif line_split[0] == "Host":
            if len(line_split) == 3:  # if the list contains three elements, the last one should be port, I hope so.
                host = f"{line_split[1][1:]}:{line_split[2]}"  # format the url to IP or Domain name:Port, e.g. 127.0.0.1:8765
            else:
                host = line_split[1]  # otherwise, access the host directly
    if method in ("GET", "HEAD", "POST"):
        req_dict["method"] = method
        req_dict["file"] = file
        req_dict["version"] = version
        req_dict["range"] = ranges
        req_dict["host"] = host
    else:
        req_dict["method"] = None  # for unsupported method, set to None     
    return req_dict


# example of response, parse_response is to help format the response like following:
    # HTTP/1.0 200 OK
    # Date: Sun, 07 Oct 2018 23: 38: 23 CST
    # Server: Darwin/17.7.0 (posix)
    # Connection: close
    # Content-Type: text/html
    # Content-Length: 448 B
    # Content-Encoding: utf-8

# parse string into response format
def parse_response(status_code, connection_status="close"):
    # supported status code: 200, 206, 302, 400, 404, 405, 505
    status_statement = {200: "OK", 405: "Method Not Allowed", 404: "Not Found", 400: "Bad Request",\
                        505: "HTTP Version Not Supported", 206: "Partial Content", 302: "Found"}
    if status_code == 206:  # range header is only supported in HTTP/1.1
        status = f"HTTP/1.1 {status_code} {status_statement[status_code]}"  # format, e.g. HTTP/1.0 200 OK   
    else:
        status = f"HTTP/1.0 {status_code} {status_statement[status_code]}"  # for HTTP/1.0
    connection = f"Connection: {connection_status}"
    date = f"Date: "+ time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime())
    server = f"Server: {platform.system()}/{platform.release()} ({os.name})" 
    response = f"{status}\r\n{date}\r\n{server}\r\n{connection}"
    return response


# handle the POST
def post_handler():
    return parse_response(405) + "\r\n\r\n"


# handle the GET
def get_handler(file, has_range=None, host=""):
    global last_visited
    if file == "./...":  # back to root directory 
        last_visited = None
        file = "./"
    if not os.path.isdir(file) and not os.path.isfile(file):  # no such file or directory 
        return error_handler(404)
    else:
        content = render_page(file, isdir=os.path.isdir(file))  # render a web page
        if content == -1:
            return error_handler(404)
        if has_range:  # partial content
            partial_content = []  # to record partial content
            for r in has_range:  
                # convert to bytes then convert back with partial content
                partial_content += [content.encode('utf-8')[r[0]:r[1]].decode('utf-8')]
            content = partial_content
    response = parse_response(200)
    if os.path.isdir(file):
        file_type = "text/html"
        # to support cookie, if last visit is not root directory,
        # then will redirect to last directory when visiting root directory
        if not last_visited or file!= "./" and last_visited != None and last_visited != file:
            last_visited = file
        elif last_visited != None and file == "./" and last_visited != "./":
            response = parse_response(302)  # For Found response
            path = copy(last_visited)
            location = f"Location: http://{host}{path[1:]}"  # Location: http://127.0.0.1:8765/<file_name>
            response += f"\r\n{location}"
            last_visited = file  # update cookie
        else:
            last_visited = None
    else:
        # for file type
        file_type = mimetypes.guess_type(file, strict=True)[0] \
            if mimetypes.guess_type(file, strict=True)[0] else 'application/octet-stream'
    content_type = f"Content-Type: {file_type}"
    content_length = f"Content-Length: {os.path.getsize(file)}"  # get file size
    encoding = f"Content-Encoding: utf-8"
    if has_range:  # Range Header
        accept_range = "Accept-Ranges: bytes"
        content_type_resp = "Content-Type: multipart/byteranges"
        file_size = os.path.getsize(file)
        response = parse_response(206) + f"\r\n{accept_range}\r\n{content_type_resp}\r\n{encoding}"
        # for partial content, every partial content should have corresponding header
        for r, part in zip(has_range, content):  # for partial content response
            content_length = f"Content-Length: {r[1]-r[0]+1}"  # e.g. Content-Length: 10
            content_type = f"Content-Range: bytes {r[0]}-{r[1]}/{file_size}"  # e.g. Content-Range: bytes 0-9/26
            response += f"\r\n\r\n{content_type}\r\n{content_length}\r\n{part}"
        return response
    else:  # common GET
        return response + f"\r\n{content_type}\r\n{content_length}\r\n{encoding}\r\n\r\n{content}"


# handle the HEAD
def head_handler(file):
    response = parse_response(200)
    if not os.path.isdir(file) and not os.path.isfile(file):  # if file is neither a directory or file, it dosen't exist.
        return error_handler(404)
    if os.path.isdir(file):
        file_type = "text/html"  # set content type of directory to be text/html so that the page can be displayed normally.
    else:
        file_type = mimetypes.guess_type(file, strict=True)[0] \
            if mimetypes.guess_type(file, strict=True)[0] else 'application/octet-stream'
    content_type = f"Content-Type: {file_type}"
    content_length = f"Content-Length: {os.path.getsize(file)}"
    encoding = f"Content-Encoding: utf-8"
    return response + f"\r\n{content_type}\r\n{content_length}\r\n{encoding}"


# handle the error or unknown cases
def error_handler(error_code):
    return parse_response(error_code) + "\r\n\r\n"


# render the web page, used when handling GET
def render_page(file, isdir=False):
    if isdir:  # directory
        file_list = os.listdir(file)  # get the files in the directory, as a list
        link_list = "".join([f"<a href='./{f}'>{f}</a></br>" for f in file_list])  # catenate strings to a single string
        content = f"<!DOC HTML><html><head><title>Index of {file}</title></head>" + "</title></head>" + \
            f"<h1>Index of {file} </h1><hr><pre>{link_list}</pre><hr></body></html>"
        print(content)
    else:  # file
        try:
            with open(file, "r", encoding="utf-8") as f:  # open file, "r"-> read mode, use utf-8 encoding
                content = f.read()  # read the content of the file
        except FileNotFoundError:  # if file not found, throw an exception, return value -1
            return -1
    return content  # return the content


# start the http server
async def http_server(host='localhost', port=6666):
    server = await asyncio.start_server(request_handler, host, port)
    print(f"HTTP server is listening on {host}:{port}")
    async with server:
        await server.serve_forever()  # server runs forever

# main
if __name__ == "__main__":
    host = 'localhost'  # host
    port = 8765  # port
    asyncio.run(http_server(host, port)) # run the server with given host and port

