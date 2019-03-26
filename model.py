#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
from common import myhash, PDEBUG
import re
import sys
import codecs


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

    name = name.strip()
    # remove BOMs first
    bts = name.encode()
    if bts[0:3] == codecs.BOM_UTF8:
        name = bytes.decode(bts[3:])
        bts = name.encode()

    # replace some  charachters.
    for (k, v) in reps:
        name = name.replace(k, v)

    # merge multiple white spaces
    name = ' '.join(name.strip().split())

    m = r_match_book.match(name)
    if m:
        name = m.group(1)

    return name.strip()


def getDBPath(readonly=False):
    """Return path of database.
    """
    if sys.platform == 'darwin':
        path = '%s/Library/Application Support/Klip/' % os.getenv("HOME")
    else:
        raise Exception("Platform %s not support." % sys.platform)

    if not os.path.exists(path):
        os.mkdir(path)
    path += 'klip.db'

    if readonly:
        path += '?mode = ro'

    return path


CLIP_TABLE = 'clippings'

CLIP_CREATE = '''
create table if not exists %s
    (
      ID INTEGER PRIMARY KEY  AUTOINCREMENT,
      BOOK TEXT,
      POS INTEGER,
      TIMESTAMP TEXT,
      CONTENT TEXT
    );
''' % CLIP_TABLE

CLIP_INSERT_FMT = 'insert into %s values ' % CLIP_TABLE + \
    '''(%u, '%s', '%s', '%s', '%s');'''

QUERY_CLIP_FROM_ID = "select id, book from %s where ID = " % CLIP_TABLE + "%u"
QUERY_CLIP_FROM_BOOK = u"select content from %s where BOOK = " % CLIP_TABLE + "'%s'"

BOOK_TABLE = 'books'
BOOK_CREATE = '''
create table if not exists %s
(
      ID INTEGER PRIMARY KEY AUTOINCREMENT,
      NAME TEXT
)
''' % BOOK_TABLE
BOOK_INSERT_FMT = 'insert into %s values ' % BOOK_TABLE + \
    '''(%u, '%s');'''
QUERY_BOOK_FMT = "select id, book from %s where ID = " % BOOK_TABLE + "%u"


class BookIter(object):
    """
    """

    def __init__(self, cursor):
        self._cursor = cursor
        super(BookIter, self).__init__()
        self.id = None
        self.book = None

    def next(self):
        """Return next book of format (ID, NAME), or None if no books
        """
        res = self._cursor.fetchone()
        if res:
            self.id = res[0]
            self.book = res[1]
            return True

        return False


class ClipIter(object):
    """
    """

    def __init__(self, cursor):
        self._cursor = cursor
        super(ClipIter, self).__init__()
        self.id = None
        self.book = None
        self.pos = None
        self.content = None

    def next(self):
        """Return next book of format (ID, NAME), or None if no books
        """
        res = self._cursor.fetchone()
        if res:
            self.id = res[0]
            self.book = res[1]
            self.pos = res[2]
            self.content = res[3]
            return True

        return False


class KlipModel(object):
    def __init__(self, readonly=False):
        """
        """
        super(KlipModel, self).__init__()
        self.conn = sqlite3.connect(getDBPath(readonly))
        self.c = self.conn.cursor()
        self.__execute__(CLIP_CREATE, True)
        self.__execute__(BOOK_CREATE, True)

    def __execute__(self, sql, commit=True):
        """
        Execute sql, and commit commit if asked.
        """
        try:
            cursor = self.c.execute(sql)
        except sqlite3.IntegrityError as e:
            print('DUP: %s' % e)
        except Exception as e:
            print('FATAL: %s -- %s' % (e, sql))
        else:
            if commit:
                self.conn.commit()

        return self.c

    def __del__(self):
        """
        """
        self.conn.commit()
        self.conn.close()
        pass

    def __addEntry__(self, book, pos, date, clip):
        """Check if book is already in store, and returns a tuple to indicate if
        clip and book are new: (new_book, new_clip).

        Arguments:

        - `book`: name of book
        - `pos`: start position of clip
        - `date`: adding date
        - `clip`: content of clipping
        """

        cur = self.__execute__('''select id from books where NAME = '%s'
''' % book)

        row = cur.fetchone()
        if row is None:
            new_book = True
            self.__execute__('''insert into books values (NULL, '%s')
''' % book)
        else:
            new_book = False

        cur = self.__execute__('''
select id from clippings where book = '%s' and content = '%s'
''' % (book, clip))

        row = cur.fetchone()

        if row is None:
            self.__execute__('''
insert into clippings values (NULL, '%s', %u, '%s', '%s')
''' % (book, pos, date, clip), False)
            new_clip = True
        else:
            new_clip = False

        return (new_book, new_clip)


    def __cleanClipsById__(self, ids):
        if ids is None or len(ids) == 0:
            return

        PDEBUG('ids: %s', ids)
        id_strs = []
        for id in ids:
            id_strs.append("%d" % id)

        sql = '''delete from clippings where id in (%s)''' % ", ".join(id_strs)

        self.__execute__(sql, True)
        pass

    def loadFile(self, path):
        """Load clippings from file.

        Arguments:

        - `path`: path of file
        """
        books_added = 0
        records_added = 0
        books_to_clean = set()
        tmp_fd = open('/tmp/tmp_write.txt', 'w')

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

                        tmp_fd.write(book + "\n")

                        bts=book.encode()
                        if bts[0:3] == codecs.BOM_UTF8:
                            PDEBUG('oops: ')
                            PDEBUG('%X-%X-%X', bts[0], bts[1], bts[2])

                            sys.exit()


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
                            self.__addEntry__(book, start, time, mark)

                        if new_book:
                            books_added += 1

                        if new_clip:
                            books_to_clean.add(book)
                            records_added += 1

        for book in books_to_clean:
            self.cleanUpBook(book)

        print('Total books added: %d, clips added:%d' %
              (books_added, records_added))

        return (books_added, records_added)


    def cleanUpBooks(self):
        """
        """
        iter = self.getBooks()
        while iter.next():
            self.cleanUpBook(iter.book)

    def cleanUpBook(self, book):
        """
        """
        PDEBUG('Cleaning book: %s', book)
        clips = {}  # pos - (id, content)
        dup_id = []

        iter = self.getClipsByName(book)
        while iter.next():
            id = iter.id
            pos = iter.pos
            content = iter.content.strip(u' "“')
            if iter.pos in clips:
                old = clips[pos]
                old_id = old[0]
                old_content = old[1]

                PDEBUG('POS: %d -- %d\nOLD: [%d]%s\n[%d]NEW:%s', pos,
                       old_id,
                       iter.pos, id,
                       old_content, content)

                if old_content.startswith(content) or \
                   content.endswith(old_content):
                    # existing one should be replaced with new one
                    dup_id.append(old_id)
                    clips[pos] = (id, content)
                    continue
                elif content.startswith(old_content) or \
                        old_content.endswith(content):
                    # new one should be dropped..
                    dup_id.append(id)
                    continue

            clips[iter.pos] = (id, content)

        if dup_id:
            self.__cleanClipsById__(dup_id)

        pass

    def getBooks(self):
        """Return iterator of books.
        """
        cur = self.conn.execute('''select ID, NAME from books;''')
        return BookIter(cur)

    def getClipsByName(self, book):
        sql = '''select id, book, pos, content from clippings'''
        if book is not None:
            sql += ''' where book = '%s'  ''' % book

        cursor = self.conn.execute(sql)
        return ClipIter(cursor)
