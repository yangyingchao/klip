#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import codecs

from common import myhash, PDEBUG


PAGE_SIZE = 4096

R_MATCH_ENTRY = re.compile(
    u'^(.*?)\n- (.*?) \\| (.*?)\n(.*?)\n==========', re.DOTALL | re.MULTILINE)

R_MATCH_POS = re.compile(u'.*?位置 #(\d+).*')
R_MATCH_PAGE = re.compile(u'.*?第 (\d+).*')


def handleStr(ins):
    """

    Arguments:
    - `s`:
    """
    ins.strip()

    out = ''

    for s in ins:
        if s == "'":
            s = '"'
        out += s
    return out


boms = [codecs.BOM_UTF8]
reps = [('（', '('), ('）', ')'), ('（', '('), ('）', ')')]
r_match_book = re.compile('(.*?)\(.*?\)', re.DOTALL)


def process_book_name(name):
    """
    Process book name.
    Arguments:
    - `name`:
    """

    PDEBUG('Processing book: %s', name)

    # replace some  charachters.
    for (k, v) in reps:
        name = name.replace(k, v)

    # merge multiple white spaces
    name = ' '.join(name.strip().split())

    m = r_match_book.match(name)
    if m:
        name = m.group(1)

        # remove BOMs first
    for bom in boms:
        if name.startswith(str(bom)):
            name = name[len(bom):]

    return name.strip()


class KlipController(object):
    """
    """

    def __init__(self, model_):
        """
        Initialize KlipController
        Arguments:
        """
        self.model = model_
        super(KlipController, self).__init__()

    def loadFile(self, path):
        """Load clippings from file.

        Arguments:

        - `path`: path of file
        """
        books_added = 0
        records_added = 0

        with open(path) as fd:
            while True:
                content = fd.read(PAGE_SIZE)
                if content is None:
                    break
                if len(content) == 0:
                    break
                pos = 0
                while True:
                    m = R_MATCH_ENTRY.search(content, pos)
                    if m is None:
                        new_content = fd.read(PAGE_SIZE)
                        if len(new_content) == 0:
                            print('New books: %d, new records: %d' %
                                  (books_added, records_added))
                            print('EOF reached...')
                            return (books_added, records_added)
                        else:
                            content = content[pos:] + new_content
                            pos = 0
                    else:
                        book = handleStr(process_book_name(m.group(1)))
                        page = handleStr(m.group(2).strip())
                        time = handleStr(m.group(3).strip())
                        mark = handleStr(m.group(4).strip())
                        pos = m.end(0)

                        if len(mark) == 0:
                            continue

                        res = R_MATCH_POS.match(page)
                        if res is None:
                            res = R_MATCH_PAGE.match(page)
                            if res is None:
                                PDEBUG('oops: %s -- %s', book, page)
                                sys.exit(1)

                        start = int(res.group(1))

                        (new_book, new_clip) = \
                            self.model.addEntry(book, start, time, mark)

                        if new_book:
                            books_added += 1

                        if new_clip:
                            records_added += 1

        print('Total books added: %d, clips added:%d'%(books_added, records_added))
        return (books_added, records_added)


    def getBooks(self):
        """
        """
        return self.model.getBooks()
        pass

    def getClips(self, book):
        """
        """
        return self.model.getClips(book)
        pass
