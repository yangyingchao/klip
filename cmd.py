#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback
from common import getClipPath

controller = None
stop=False

def loadFile(args):
    """Load clippings from args[0]

    Arguments:
    - `args`:
    """
    if args and len(args) > 0:
        path = args[0]
    else:
        path = getClipPath()

    controller.loadFile(path)
    pass


def showHelp(args):
    """
    """
    print('Not implemented...')
    pass


def exitFunc(args):
    """

    Arguments:
    - `args`:
    """
    global stop
    stop = True
    pass


def showBooks():
    print('Showing books:')
    counter = 0
    iter = controller.getBooks()
    while True:
        (id, book) = iter.next()
        if id:
            print('    [%d] -- %s'%(id, book))
            counter += 1
        else:
            break

    print('\nTotal books: %d'%(counter))
    pass

def showClips(book=None):
    print('Showing clips:')
    counter = 0
    iter = controller.getClips(book)
    while True:
        (id, book, clip) = iter.next()
        if id:
            print('    [%d] -- %s -- %s'%(id, book, clip))
            counter += 1
        else:
            break

    print('\nTotal books: %d'%(counter))
    pass

def showFunc(args):

    if args:
        target = args[0].lower()
        if target == "books":
            showBooks()
        elif target == "clips":
            if len(args) > 1:
                showClips(" ".join(args[1:]))
            else:
                showClips()
        else:
            raise Exception("not implemented: %s" % target)
    else:
        showBooks();

    pass

handlers = {
    "load": loadFile,
    "/h": showHelp,
    "exit":exitFunc,
    "quit":exitFunc,
    "show":showFunc,
}


def startCMD(controller_):
    global controller
    controller = controller_
    print('Input your commands here, type "/h" for help.. ')
    while not stop:
        try:
            print('>')
            line = sys.stdin.readline().strip()
            array = line.split()
            l = len(array)
            if l == 0:
                continue

            cmd = array[0].lower()
            args = array[1:] if l > 1 else None
            handler = handlers.get(cmd, None)
            if handler is None:
                print('CMD: %s not implemented'%(cmd))
                continue

            handler(args)
        except Exception as e:
            print ('str(Exception):\t %s' % str(Exception)                  )
            print ('str(e):\t\t%s'% str(e)                                 )
            print ('repr(e):\t%s'% repr(e)                                 )
            print ('traceback.print_exc():%s'% traceback.print_exc()       )
            print ('traceback.format_exc():\n%s' % traceback.format_exc())
    pass
