#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import re
import traceback
import struct
from klip_common import PDEBUG
import json
import socket

model = None


def getBooks():
    """Get list of books (id, name).
    """
    ret = {}
    books = []
    iter = model.getBooks()
    while iter.next():
        books.append((iter.id, iter.name))

    ret['books'] = books
    return ret


def getClips(book_id):
    """Get list of clips.

    Arguments:
    - `book_id`: id of book, if this is given, returns clips of specified book.
    """
    ret = {}
    clips = []
    it = model.getClipsByBookId(book_id)
    while it.next():
        clips.append((it.id, it.content))
        pass

    ret['clips'] = clips
    return ret


def processQuery(j):
    """
    """
    PDEBUG('Query: %s', j)

    r = {}
    cmd = j.get('cmd', None)
    if cmd is None:
        r['err'] = 'No command is specified.'
    elif cmd == 'get-books':
        r = getBooks()
        pass
    elif cmd == 'get-clips':
        book_id = j.get('book-id', None)
        if book_id is None:
            r['err'] = 'Book id not specified.'
        else:
            r = getClips(book_id)
        pass
    else:
        r['err'] = 'Unsupported command: %s' % cmd

    return json.dumps(r)
    pass


def startServer(model_):
    """
    """
    global model
    model = model_

    HOST, PORT = "localhost", 9999

    with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                     struct.pack('ii', 0, 0))

        s.bind((HOST, PORT))
        s.listen(1)
        PDEBUG('Listening on %s:%d', HOST, PORT)
        while True:
            conn, addr = s.accept()
            with conn:
                PDEBUG('Connected by: %s', addr)
                data = ''

                while True:

                    if len(data) < 4:  # header length
                        # Read Length, 4 bytes
                        data = conn.recv(1024)
                        if not data:
                            PDEBUG('No data, break...')
                            break

                    PDEBUG('LEN: %d' % (len(data)))
                    PDEBUG('DATA: %s', data)

                    # Now parse header...
                    total = len(data)
                    l = struct.unpack_from('!I', data, 0)[0]
                    total -= 4
                    PDEBUG('L: %d, total: %d' % (l, total))

                    body = data[4:]
                    PDEBUG('BODY: %s', body)
                    if total < l:
                        expected = l - total
                        while expected > 0:
                            PDEBUG('1: Needs to read %d bytes...', expected)
                            data = conn.recv(1024)
                            PDEBUG('Got data: %s, len: %d', data, len(data))
                            to_copy = min(len(data), expected)
                            expected -= to_copy
                            body += data[:to_copy]
                            PDEBUG('2: Needs to read %d bytes...', expected)

                            if expected == 0:
                                data = data[to_copy:]
                    else:
                        data = data[4 + l:]

                    # Now we should have a complete json string...
                    PDEBUG('BODY: %s', body)
                    j = json.loads(body)

                    PDEBUG('GOT: %s' % (j))

                    ret = processQuery(j)
                    PDEBUG('RET: %s' % (ret))

                    ret_txt = ret.encode()
                    rsp = struct.pack('!I', len(ret_txt))
                    rsp += ret_txt

                    conn.sendall(rsp)


if __name__ == '__main__':
    startServer(None)
