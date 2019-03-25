#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
from common import myhash


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
      ID INTEGER PRIMARY KEY AUTOINCREMENT,
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

    def next(self):
        """Return next book of format (ID, NAME), or None if no books
        """
        res = self._cursor.fetchone()
        if res:
            return (res[0], res[1])
        return (None, None)


class ClipIter(object):
    """
    """

    def __init__(self, cursor):
        self._cursor = cursor
        super(ClipIter, self).__init__()

    def next(self):
        """Return next book of format (ID, NAME), or None if no books
        """
        res = self._cursor.fetchone()
        if res:
            return (res[0], res[1], res[2])
        return (None, None, None)


class KlipModel(object):
    def __init__(self, readonly=False):
        """
        """
        super(KlipModel, self).__init__()
        self.conn = sqlite3.connect(getDBPath(readonly))
        self.c = self.conn.cursor()
        self.execute(CLIP_CREATE, True)
        self.execute(BOOK_CREATE, True)

    def execute(self, sql, commit=True):
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

    def getBooks(self):
        """Return iterator of books.
        """
        cur = self.execute('''select ID, NAME from books;''')
        return BookIter(cur)

    def cleanup(self):
        """ Clean up model and database.
        """
        pass

    def addEntry(self, book, pos, date, clip):
        """Check if book is already in store, and returns a tuple to indicate if
        clip and book are new: (new_book, new_clip).

        Arguments:

        - `book`: name of book
        - `pos`: start position of clip
        - `date`: adding date
        - `clip`: content of clipping
        """

        cur = self.execute('''select id from books where NAME = '%s'
''' % book)

        row = cur.fetchone()
        if row is None:
            new_book = True
            self.execute('''insert into books values (NULL, '%s')
''' % book)
        else:
            new_book = False

        cur = self.execute('''
select id from clippings where book = '%s' and content = '%s'
''' % (book, clip))

        row = cur.fetchone()

        if row is None:
            self.execute('''
insert into clippings values (NULL, '%s', %u, '%s', '%s')
''' % (book, pos, date, clip), False)
            new_clip = True
        else:
            new_clip = False

        return (new_book, new_clip)

    def getClips(self, book):
        sql='''select id, book, content from clippings'''
        if book is not None:
            sql += ''' where book = '%s'  ''' % book

        cursor = self.execute(sql)
        return ClipIter(cursor)
