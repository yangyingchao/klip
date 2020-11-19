#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import traceback


def getClipPath():
    """Return path of "My Clippings.txt", written by Kindle.
    """
    path = None

    if sys.platform == 'darwin':
        path = "/Volumes/Kindle/documents/My Clippings.txt"
    elif sys.platform == 'linux':
        path = '/run/media/%s/Kindle/documents/My Clippings.txt' % (os.getenv('USER'))
    else:
        Exception("Platform %s not support." % sys.platform)

    if os.path.exists(path):
        return path

    return os.path.join(os.path.dirname(__file__), "My Clippings.txt")


def getKindleDir():
    return os.path.dirname(getClipPath())


def myhash(value):
    """

    Arguments:
    - `value`:
    """
    return hash(value) % ((sys.maxsize + 1) * 2)


debug_mode = True


# import  traceback
def PDEBUG(fmt, *args):
    """
    Utility to show debug logs.
    """
    if not debug_mode:
        return

    stack = traceback.extract_stack(None, 2)[0]
    try:
        msg = fmt % args
    except:
        msg = "Failed to format string.."
    finally:
        print("DEBUG - (%s:%d -- %s): %s" %
              (stack[0], stack[1], stack[2], msg))

