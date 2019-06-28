#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import traceback
from klip_common import getClipPath

model = None

stop = False


def loadFile(args):
    """Load clippings from file (if specified), or from default file.
    """
    if args:
        path = args[0]
    else:
        path = getClipPath()

    model.loadFile(path)
    pass


def showHelp(args):
    """  Show  help message.
    """
    print('Show help message...\n')

    for key in handlers.keys():
        func = handlers[key]
        print('    %s: %s' % (key, func.__doc__))
    pass


def exitFunc(args):
    """exit klip.
    """
    global stop
    stop = True
    pass


def showBooks():
    """ Show books.
    """
    print('Showing books:')
    counter = 0
    iter = model.getBooks()
    while iter.next():
        counter += 1
        print('    [%d] -- %s' % (iter.id, iter.name))

    print('\nTotal books: %d' % (counter))
    pass


def showClipIter(it):
    idx = 0
    while it.next():
        idx += 1
        print('    [%d] -- %s -- %s' % (it.id, it.pos, it.content))

    print('\nTotal clippings: %d' % (idx))
    return idx


def showClipsByName(book):
    print('Showing clips from book: %s' % book)
    num = showClipIter(model.getClipsByName(book))
    return num


def showClips():
    """ Show Clips from all books.
    """
    counter_book = 0
    counter_clips = 0
    iter_book = model.getBooks()
    while iter_book.next():
        counter_book += 1
        counter_clips += showClipsByName(iter_book.book)

    print('\nTotal books: %d, total clips: %d' % (counter_book, counter_clips))


def showFunc(args):
    """ Show books or clips.
    eg, show books
        show clips
    """
    if args:
        target = args.pop(0).lower()
        if target == "books":
            showBooks()
        elif target == "clips":
            if args:
                book = None
                if len(args) == 1:
                    m = re.match("\\[(\\d+)\\]", args[0])
                    if m:
                        bi = model.getBookById(int(m.group(1)))
                        if bi.next():
                            book = bi.book

                if book is None:
                    book = " ".join(args[1:])
                showClipsByName(book)
            else:
                showClips()
        else:
            raise Exception("not implemented: %s" % target)
    else:
        showBooks()

    pass


def showGUI(args):
    """Show GUI
    """
    from gui import startGUI
    startGUI(model)
    pass


def cleanupCallback(book, lst):
    if lst:
        print('Going to remove following items for book: %s\n' % book)
        idx = 1
        for (keep, drop) in lst:
            print('[%d]' % idx)
            print('    KEEP: %s' % (keep))
            print('    DROP: %s' % (drop))
            idx += 1
            print('')

        print('\nContintue? Y/[N]')

        line = sys.stdin.readline().lower().strip()
        if len(line) == 0:
            return True
        if len(line) == 1 and line[0] == 'y':
            return True
        return False
    return True


def cleanUp(books=None):
    """Clean clippings, by removing duplicated records.
    """
    if books:
        for book in books:
            model.cleanUpBook(book, cleanupCallback)
    else:
        model.cleanUpBooks(cleanupCallback)


def searchClips(args):
    """Search clippings.
    Arguments:
    - `args`: List of keywords.
    """
    showClipIter(model.searchClips(args))


handlers = {
    "load": loadFile,
    "help": showHelp,
    "/h": showHelp,
    "exit": exitFunc,
    "quit": exitFunc,
    "q": exitFunc,
    "show": showFunc,
    "clean": cleanUp,
    "gui": showGUI,
    'search': searchClips,
}


def startCMD(model_):
    global model
    model = model_
    print('Input your commands here, type "/h" for help.. ')
    while not stop:
        try:
            print('>')
            line = sys.stdin.readline().strip()
            args = line.split()
            if not args:
                continue

            cmd = args.pop(0).lower()
            handler = handlers.get(cmd, None)
            if handler is None:
                print('CMD: %s not implemented' % (cmd))
                continue

            handler(args)
        except Exception as e:
            print('str(Exception):\t %s' % str(Exception))
            print('str(e):\t\t%s' % str(e))
            print('repr(e):\t%s' % repr(e))
            print('traceback.print_exc():%s' % traceback.print_exc())
            print('traceback.format_exc():\n%s' % traceback.format_exc())
    pass
