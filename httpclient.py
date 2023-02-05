#!/usr/bin/env python3
# coding: utf-8
# Copyright 2023 Jordan Van Den Bruel
#
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
# urllib.parse documentation used to find functions 'quote', 'unquote', and 'urlencode'
import urllib.parse
import json


def help():
    print("httpclient.py [GET/POST] [URL]\n")


class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body


class HTTPClient(object):
    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        # get first line of response and capture each string
        code_line, _ = data.split('\r\n', 1)
        code = code_line.split(' ')
        # ensure there are at least 3 items (HTTP/1.1 CODE MESSAGE)
        if len(code) < 3:
            return 500
        # ensure request is HTTP/1.*
        if 'HTTP/1.' not in code[0].upper():
            return 505  # todo correct code?
        # ensure second value is number
        if not code[1].isnumeric():
            return 500

        return int(code[1])

    def get_body(self, data):
        _, body = data.split('\r\n\r\n', 1)
        return body

    def create_query(self, data):
        query = '?'
        for key in data:
            query += '{}={}&'.format(key, urllib.parse.quote(data[key]))
        return query[:-1]

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        code = 500
        body = ""

        # determine host port, and path
        url = urllib.parse.urlparse(url)
        hostname = url.hostname
        port = url.port

        # give default port if not included
        if port == None and url.scheme == 'http':
            port = 80
        elif port == None and url.scheme == 'https':
            port = 443

        # return 400 with no body if missing hostname or not given http(s) scheme
        if hostname == None or port == None:
            return HTTPResponse(400, body)
        path = url.path
        if path == None or path == "":
            path = '/'

        # add query if given in args
        if type(args) is dict:
            path += self.create_query(args)

        # connect
        self.connect(hostname, port)

        # form start of request
        request = 'GET {} HTTP/1.1\r\n'.format(path)

        # add host, user agent, connection, and accept as header
        request += 'Host: {}:{}\r\nUser-Agent: CMPUT404-Requester-Thing\r\nConnection: close\r\nAccept: */*\r\n\r\n'.format(
            hostname, port)

        # send the request
        self.sendall(request)

        # get the response
        response = self.recvall(self.socket)
        self.close()

        # ensure there is a response
        if len(response) == 0:
            return HTTPResponse(code, body)

        # print the response
        print(response)

        code = self.get_code(response)
        # remove url encoding in the body
        body = urllib.parse.unquote(self.get_body(response))

        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        code = 500
        body = ""

        # determine host port, and path
        url = urllib.parse.urlparse(url)
        hostname = url.hostname
        port = url.port

        # give default port if not included
        if port == None and url.scheme == 'http':
            port = 80
        elif port == None and url.scheme == 'https':
            port = 443

        # return 400 with no body if missing hostname or not given http(s) scheme
        if hostname == None or port == None:
            return HTTPResponse(400, body)
        path = url.path
        if path == None or path == "":
            path = '/'

        # connect
        self.connect(hostname, port)

        # form start of request
        request = 'POST {} HTTP/1.1\r\n'.format(path)

        # add host, user agent, connection, and accept as header
        request += 'Host: {}:{}\r\nUser-Agent: CMPUT404-Requester-Thing\r\nConnection: close\r\nAccept: */*\r\n'.format(
            hostname, port)

        # add content length and body
        if type(args) is dict:
            args = urllib.parse.urlencode(args)
            request += 'Content-Type: application/x-www-form-urlencoded\r\nContent-Length: '

            request += '{}\r\n\r\n{}'.format(len(args), args)
        else:
            request += "Content-Length: 0\r\n\r\n"

        # send the request
        self.sendall(request)

        # get the response
        response = self.recvall(self.socket)
        self.close()

        # ensure there is a response
        if len(response) == 0:
            return HTTPResponse(code, body)

        # print the response
        print(response)

        code = self.get_code(response)
        # remove url encoding in the body
        body = urllib.parse.unquote(self.get_body(response))

        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command(sys.argv[2], sys.argv[1]))
    else:
        print(client.command(sys.argv[1]))
