#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
from klip_common import PDEBUG
import re
import enum
import codecs

PAGE_SIZE = 4096

R_MATCH_ENTRY = re.compile(u'^(.*?)\n- (.*?) \\| .*? (.*?)\n(.*?)\n==========',
                           re.DOTALL | re.MULTILINE)

R_MATCH_POS = re.compile(u'.*?位置 #(\d+(?:-\d+)?).*?的(标注|笔记)')
R_MATCH_PAGE = re.compile(u'.*?第 (\d+).*?的(标注|笔记)')

KLIP_DATA_VERSION = 1


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
    return out.strip()


boms = [codecs.BOM_UTF8]
reps = [('（', '('), ('）', ')'), ('（', '('), ('）', ')')]
r_match_book = re.compile('(.*?)\((.*?)\)', re.DOTALL)


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
    author = ''

    m = r_match_book.match(name)
    if m:
        name = m.group(1)
        author = m.group(2)

    return (name.strip(), author.strip())


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


SQL_CREATE_CLIPS = '''
create table if not exists clippings
    (
      ID INTEGER PRIMARY KEY  AUTOINCREMENT,
      BOOK ID,
      POS TEXT,
      TYPE TEXT,
      DATE TEXT,
      CONTENT TEXT
    );
'''

BOOK_TABLE = 'books'
SQL_CREATE_BOOKS = '''
create table if not exists %s
(
      ID INTEGER PRIMARY KEY AUTOINCREMENT,
      NAME TEXT,
      AUTHOR TEXT
)
''' % BOOK_TABLE


class BookIter(object):
    """
    """

    def __init__(self, cursor):
        self._cursor = cursor
        super(BookIter, self).__init__()
        self.id = None
        self.name = None
        self.author = None

    def next(self):
        """Return next book of format (ID, NAME), or None if no books
        """
        res = self._cursor.fetchone()
        if res:
            self.id = res[0]
            self.name = res[1]
            self.author = res[2]
            return True

        return False


class Clip(object):
    def __init__(self, book, id, pos, typ, date, content):
        super(Clip, self).__init__()
        self.book = book
        self.id = id
        self.pos = pos
        self.typ = typ
        self.date = date
        self.content = content


class ClipIter(object):
    """
    """

    def __init__(self, cursor):
        self._cursor = cursor
        super(ClipIter, self).__init__()
        self.id = None
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


class Action(enum.Enum):
    APPEND = 0
    USE_NEW = 1
    USE_OLD = 2


class Range(object):
    def __init__(self, start, end):
        super(Range, self).__init__()
        self._start = start
        self._end = end

    def __hash__(self):
        return self._start << 32 | self._end

    def covers(self, other):
        """Check if this object covers the other object.
        """
        return self._start <= other._start and self._end >= other._end


class KlipModel(object):
    def __init__(self, readonly=False, trial=False):
        """
        """
        super(KlipModel, self).__init__()

        self.conn = None
        self._book_cache = {}

        # trial is used to make lsp happy...
        if trial:
            return
        else:
            self.__open__()

    def __open__(self):
        self.conn = sqlite3.connect(getDBPath(False))

        self.__execute__(
            '''
create table if not exists version
(
        major int
);
''', True)

        ans = self.__execute__('select major from version;').fetchone()
        if ans is None or ans[0] == KLIP_DATA_VERSION:
            self.__execute__(
                '''insert into version values (%d)''' % KLIP_DATA_VERSION,
                True)
            self.__execute__(SQL_CREATE_CLIPS, True)
            self.__execute__(SQL_CREATE_BOOKS, True)

            # Things in blacklist: bad or incomplete records.
            self.__execute__(
                '''create table  if not exists blacklist as
select * from clippings limit 0''', True)
            return

        version = ans[0]
        print('Upgrade needed, not implemented.. %d -- %d' %
              (version, KLIP_DATA_VERSION))

    def __execute__(self, sql, commit=True):
        """
        Execute sql, and commit commit if asked.
        """
        cursor = None
        try:
            cursor = self.conn.execute(sql)
        except sqlite3.IntegrityError as e:
            print('DUP: %s' % e)
        except Exception as e:
            print('FATAL: %s -- %s' % (e, sql))
        else:
            if commit:
                self.conn.commit()

        return cursor

    def __del__(self):
        """
        """
        if self.conn:
            self.conn.commit()
            self.conn.close()
        pass

    def __addEntry__(self, book, author, pos, typ, date, clip):
        """Check if book is already in store, and returns a tuple to indicate if
        clip and book are new: (new_book, new_clip).

        Arguments:

        - `book`: name of book
        - `pos`: start position of clip
        - `date`: adding date
        - `clip`: content of clipping
        """
        new_book = False
        book_id = self._book_cache.get(book, None)

        if book_id is None:
            cur = self.__execute__(
                '''select id, author from books where NAME = '%s' ''' % book)
            row = cur.fetchone()
            if row is None:
                self.__execute__('''insert into books values (NULL, '%s', '%s')  ''' %
                                 (book, author))
                cur = self.__execute__(
                    '''select id, author from books where NAME = '%s' ''' % book)
                row = cur.fetchone()
                book_id = row[0]
                self._book_cache[book] = book_id
            else:
                book_id = row[0]
                self._book_cache[book] = book_id

                if row[1] is None:  # older version does not have AUTHOR field...
                    # BUG: same title from different authors??
                    self.__execute__(
                        '''update books set author = '%s' where id = %d ''' %(
                        author, book_id))

        # TODO: Position (range) is checked to decide if contents exists or not.
        #       Similarity of contents should be checked too...

        # check if record is in blacklist.
        cur = self.__execute__('''
select id from blacklist where book_id = '%d' and pos = '%s'
''' % (book_id, pos))

        row = cur.fetchone()

        if row is not None:
            # item is in blacklist, means similar content exists...
            new_clip = False
        else:
            cur = self.__execute__('''
    select id from clippings where book_id = %d and pos = '%s'
    ''' % (book_id, pos))

            row = cur.fetchone()

            if row is None:
                self.__execute__(
                    '''
    insert into clippings values (NULL, %d, '%s', '%s', '%s', '%s')
    ''' % (book_id, pos, typ, date, clip), False)
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
            id_strs.append("'%d'" % id)

        sql = '''insert into blacklist select * from clippings where id in (%s)''' % ", ".join(
            id_strs)
        self.__execute__(sql, False)

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

        PDEBUG('Loading from file: %s', path)

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
                        (book, author) = process_book_name(m.group(1))
                        book = handleStr(book)
                        author = handleStr(author)
                        page = handleStr(m.group(2).strip())
                        time = handleStr(m.group(3).strip())
                        mark = handleStr(m.group(4).strip())
                        pos = m.end(0)

                        bts = book.encode()
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

                        pos_str = res.group(1)
                        typ_str = res.group(2)

                        (new_book, new_clip) = \
                            self.__addEntry__(
                                book, author, pos_str, typ_str, time, mark)

                        if new_book:
                            books_added += 1

                        if new_clip:
                            books_to_clean.add(book)
                            records_added += 1

        if books_to_clean:
            PDEBUG('Books to clean: %s', books_to_clean)

        for book in books_to_clean:
            self.cleanUpBook(book)

        print('Total books added: %d, clips added:%d' %
              (books_added, records_added))

        return (books_added, records_added)

    def cleanUpBooks(self, callback=None):
        """
        """
        num = 0
        iter = self.getBooks()
        while iter.next():
            num += self.cleanUpBook(iter.name, callback)

        PDEBUG('Total %d records cleaned up.', num)
        return num

    def cleanUpBook(self, book, callback=None):
        """Clean up book
        """
        PDEBUG('Cleaning book: %s', book)
        clips = {}  # pos - (id, content)
        dup_id = []  # array of cons, where cdr should be dropped...

        iter = self.getClipsByBookName(book)
        total_clips = 0
        while iter.next():
            total_clips += 1

            id = iter.id
            pos = iter.pos

            # simply ignore it if '-' not in pos.
            if '-' not in pos:
                continue

            if pos.startswith('-'):
                continue

            pos_array = []
            for p in pos.split('-'):
                pos_array.append(int(p))

            # Find nearest position, for now, linear search, change to binary
            # search later....

            action = Action.APPEND  # 0: append, 1: use new, 2: use old
            key_new = Range(pos_array[0], pos_array[1])

            for key in clips.keys():
                if key.covers(key_new):
                    action = Action.USE_OLD
                    break
                elif key_new.covers(key):
                    action = Action.USE_NEW
                    break
                pass

            if action == Action.APPEND:
                clips[key_new] = id
            elif action == Action.USE_NEW:
                old_id = clips.pop(key)
                dup_id.append((id, old_id))
                clips[key_new] = id
            elif action == Action.USE_OLD:
                old_id = clips[key]
                dup_id.append((old_id, id))
            else:
                print('Should not be here: %s' % (action))

        ret = 0
        if dup_id:
            do_remove = True
            if callback:
                to_be_remove = []
                for (keep, drop) in dup_id:
                    clip_keep = self.getClipById(keep)
                    clip_drop = self.getClipById(drop)

                    to_be_remove.append((clip_keep.content, clip_drop.content))

                do_remove = callback(book, to_be_remove)

            if do_remove:
                ids = []
                for id in dup_id:
                    ids.append(id[1])

                self.__cleanClipsById__(ids)
                ret += len(dup_id)

        return ret

    def getBooks(self, showAll=False):
        """Return iterator of books.
        """
        if showAll:
            sql = '''select ID, NAME from books;'''
        else:
            sql = '''
select books.id, books.name, books.author
from books where exists (
select * from clippings where books.id = clippings.book_id);'''

        cur = self.__execute__(sql)
        return BookIter(cur)

    def dropBook(self, book):
        sql = '''delete from books where name = '%s' ''' % book
        self.__execute__(sql)
        pass

    def getBookById(self, id):
        """Return iterator of books.
        """
        cur = self.__execute__(
            '''select ID, NAME, AUTHOR from books where ID = %d;''' % id)
        return BookIter(cur)

    def getClipsByBookName(self, book):
        sql = '''
        select clippings.id, books.name , pos, content from clippings
inner join books on clippings.book_id = books.id and books.name = '%s'
        ''' % book
        PDEBUG('SQL: %s', sql)
        cursor = self.__execute__(sql)
        return ClipIter(cursor)

    def getClipsByBookId(self, id):
        sql = '''
        select clippings.id, books.name , pos, content from clippings
inner join books on clippings.book_id = books.id and books.id = %d
        ''' % id
        PDEBUG('SQL: %s', sql)
        cursor = self.__execute__(sql)
        return ClipIter(cursor)

    def getClipById(self, id):
        sql = '''
        select books.name, pos, type, date, content from clippings
        inner join books on clippings.book_id = books.id and  clippings.id = %d
        ''' % id

        cursor = self.__execute__(sql)
        r = cursor.fetchone()
        return Clip(r[0], id, r[1], r[2], r[3], r[4])

    def searchClips(self, args):
        """Search clippings containing given keywords.
        """
        query = '''
        select clippings.id, books.name , pos, content from clippings
        inner join books on clippings.book_id = books.id  '''

        if args is None:
            cursor = self.__execute__(query)
        elif isinstance(args, list):
            query += "and clippings.content like ? or book like ?"
            conds = '%' + '%'.join(args) + '%'

            cursor = self.conn.execute(query, (conds, conds))
        else:
            raise Exception("Expecting a list, but got: %s." % type(args))

        return ClipIter(cursor)

    def updateClip(self, clip, text):
        """Update clip if text is changed.

        Arguments:

        - `clip`:
        - `text`:
        """
        text = handleStr(text)

        if clip.content == text:
            return False

        SQL = ''' update clippings set content = '%s' where ID = %d ''' % (
            text, clip.id)
        self.__execute__(SQL)
        clip.content = text

        return True

    def dropClip(self, clip):
        """Move specified clip into blacklist.
        """
        SQL = ''' insert into blacklist select * from clippings where ID = %d''' % clip.id
        PDEBUG('SQL: %s', SQL)
        self.__execute__(SQL)

        SQL = '''delete from clippings where ID = %d''' % clip.id
        PDEBUG('SQL: %s', SQL)
        self.__execute__(SQL)

        pass

    def newClip(self, book, content, typ, date):
        """
        Add a new clip into database.
        """
        sql = '''    insert into clippings values (NULL, '%s', '%s', '%s', '%s', '%s')
''' % (book, '0', typ, date, content)

        self.__execute__(sql)
        pass
