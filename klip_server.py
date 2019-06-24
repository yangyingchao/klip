#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import re
import traceback
from klip_common import getClipPath
from klip_model import KlipModel
import socket

model = None

### Start server ...

def processQuery():
    """
    """
    pass


def startServer(model_):
    """
    """
    HOST, PORT = "localhost", 9999

    with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    print('No data, break...')
                    break
                print('GOT: %s'%(data))
                conn.sendall(data.upper())


if __name__ == '__main__':
    startServer(None)
