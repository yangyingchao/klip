#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import wx
import wx.html2
import wx.lib.mixins.listctrl as listmix
import markdown
import os
from enum import Enum
from datetime import datetime
from klip_common import getClipPath, PDEBUG

scriptdir = os.path.dirname(os.path.realpath(__file__))
MARKDOWN_CSS = os.path.join(scriptdir, 'styles/markdown.css')
PYGMENTS_CSS = os.path.join(scriptdir, 'styles/pygments.css')


class MarkdownDoc:
    def __init__(self, markdown_css=MARKDOWN_CSS, pygments_css=PYGMENTS_CSS):

        self.inline_css = ''

        if markdown_css:
            with open(markdown_css) as markdown_css_file:
                self.inline_css += markdown_css_file.read()

        if pygments_css:
            with open(pygments_css) as pygments_css_file:
                self.inline_css += pygments_css_file.read()

        self.md = markdown.Markdown()

    def getHtml(self, text):
        self.md.reset()
        return self.md.convert(text)

    def getHtmlPage(self, text):
        return """<!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style type="text/css">
        %s
        </style>
        </head>
        <body>
        <div class="markdown-body">
        %s
        </div>
        </body>
        </html>
        """ % (self.inline_css, self.getHtml(text))


class KlipListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self,
                 parent,
                 ID,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class State(Enum):
    """State of detail window.
    """
    Initial = 0,
    Editting = 1,
    Creating = 2


class KlipDetailWindow(wx.PopupWindow):
    """Adds a bit of text and mouse movement to the wx.PopupWindow"""

    def __init__(self, parent, style):

        wx.PopupWindow.__init__(self, parent, style)

        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.state = State.Initial

        self.editor = wx.TextCtrl(self, size=(450, -1), style=wx.TE_MULTILINE)

        self.Bind(wx.EVT_TEXT, self.OnTextChange, self.editor)

        font = self.editor.GetFont()
        font.PointSize += 5
        self.editor.SetFont(font)
        self.editor.Show(False)
        self.hbox.Add(self.editor, 1, wx.EXPAND | wx.ALL, 10)

        self.md_converter = MarkdownDoc()
        self.browser = wx.html2.WebView.New(self)
        self.browser.SetMinSize(wx.Size(800, 400))
        self.hbox.Add(self.browser, 1, wx.EXPAND | wx.ALL, 10)

        self.sizer.Add(self.hbox, 1, wx.EXPAND | wx.ALL, 10)
        # type
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, "type     "), 0, wx.LEFT | wx.RIGHT,
                10)

        self.st_type = wx.StaticText(self, -1, "")
        row.Add(self.st_type, 0, wx.LEFT | wx.RIGHT, 10)
        self.sizer.Add(row, 0, wx.EXPAND | wx.ALL, 2)

        # location
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, "location"), 0,
                wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, 10)

        self.st_location = wx.StaticText(self, -1, "")
        row.Add(self.st_location, 0, wx.LEFT | wx.RIGHT, 10)

        self.sizer.Add(row, 0, wx.EXPAND | wx.ALL, 2)

        # date
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, "date     "), 0,
                wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, 10)

        self.st_date = wx.StaticText(self, -1, "")
        row.Add(self.st_date, 0, wx.LEFT | wx.RIGHT, 10)
        self.sizer.Add(row, 0, wx.EXPAND | wx.ALL, 5)

        # Button List.

        # done button
        row = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_done = wx.Button(self, -1, 'Done')
        row.Add(self.btn_done, 0, wx.ALL, 10)
        self.btn_done.Bind(wx.EVT_BUTTON, self.OnDone)

        self.btn_edit = wx.Button(self, -1, 'Edit')
        row.Add(self.btn_edit, 0, wx.ALL, 10)
        self.btn_edit.Bind(wx.EVT_BUTTON, self.OnEdit)

        self.btn_new = wx.Button(self, -1, 'New')
        row.Add(self.btn_new, 0, wx.ALL, 10)
        self.btn_new.Bind(wx.EVT_BUTTON, self.OnNew)

        self.btn_delete = wx.Button(self, -1, 'Delete')
        row.Add(self.btn_delete, 0, wx.ALL, 10)
        self.btn_delete.Bind(wx.EVT_BUTTON, self.OnDelete)

        self.sizer.Add(row, 0, wx.EXPAND | wx.ALL, 0)
        self.SetSizerAndFit(self.sizer)

    def OnTextChange(self, evt):
        text = self.editor.GetValue()
        html = self.md_converter.getHtmlPage(text)
        self.browser.SetPage(html, '')
        pass

    def Restore(self):
        """
        """
        self.editor.Show(False)
        self.browser.SetSize(wx.Size(800, 400))
        self.browser.SetMinSize(wx.Size(800, 400))

        self.state = State.Initial

        self.btn_delete.SetLabel("Delete")
        self.btn_edit.Enable(True)
        self.btn_new.Enable(True)

        self.Show(False)
        pass

    def SetupEditor(self):
        """
        """
        self.btn_edit.Enable(False)
        self.btn_new.Enable(False)

        self.btn_delete.SetLabel("Cancel")

        self.editor.Show(True)

        self.editor.SetSize(wx.Size(400, 400))
        self.browser.SetSize(wx.Size(400, 400))
        self.browser.SetMinSize(wx.Size(400, 400))

        self.Refresh()
        self.Update()
        self.Fit()

        pass

    def OnDone(self, evt):
        """Hide this window..
        """
        if self.state == State.Editting:
            self.editor.Show(False)
            text = self.editor.GetValue()
            self.parent.updateClip(self._clip, text)
        elif self.state == State.Creating:
            self.parent.newClip(
                self.editor.GetValue(),
                self.st_type.GetLabel(),
                self.st_date.GetLabel())
            pass

        self.Restore()

    def OnEdit(self, evt):
        """Edit selected clip.
        """

        if self.state == State.Editting:
            return

        self.state = State.Editting
        self.SetupEditor()

    def OnNew(self, evt):
        """Create new clip...
        """
        self.state = State.Creating

        self.editor.SetValue('')
        html = self.md_converter.getHtmlPage('')
        self.browser.SetPage(html, '')

        self.st_type.SetLabel(u'笔记')
        self.st_date.SetLabel(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.st_location.SetLabel(u'未知')

        self.SetupEditor()
        pass

    def OnDelete(self, evt):
        """Hide this window..
        """
        if self.state == State.Editting:  # label should be "Cancel"
            self.Restore()
        else:
            self.parent.dropClip(self._clip)

        self.Show(False)

    def UpdateContent(self, clip):
        self._clip = clip
        PDEBUG('POS: %s, DATE: %s', clip.pos, clip.date)
        self.editor.SetValue(clip.content)

        html = self.md_converter.getHtmlPage(clip.content)
        self.browser.SetPage(html, '')

        self.st_type.SetLabel(clip.typ)
        self.st_date.SetLabel(clip.date)
        self.st_location.SetLabel(clip.pos)

        self.Layout()
        self.sizer.Fit(self)

        pass


class KlipFrame(wx.Frame):
    """
    """

    def __init__(self, model_):
        """
        """
        self.model = model_
        self._book = None
        self._search_target = None

        super(KlipFrame, self).__init__(None, size=wx.Size(1200, 760))
        # ensure the parent's __init__ is called

        sp = wx.SplitterWindow(self, style=wx.SP_BORDER | wx.SP_3DBORDER)
        sp.SetSplitMode(wx.SPLIT_VERTICAL)
        sp.SetMinimumPaneSize(50)
        self.detailPanel = KlipDetailWindow(self, wx.SIMPLE_BORDER)
        self.SetMinSize(wx.Size(800, 600))

        # create a panel in the frame
        pnl_books = wx.Panel(sp)
        pnl_clips = wx.Panel(sp)
        pnl_clips.SetBackgroundColour(wx.Colour(255, 255, 255))

        sp.SplitVertically(pnl_books, pnl_clips,
                           int(round(self.GetSize().GetWidth() * 0.3)))

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.search = wx.SearchCtrl(pnl_books,
                                    size=(200, -1),
                                    style=wx.TE_PROCESS_ENTER)
        self.search.ShowSearchButton(True)
        self.search.ShowCancelButton(True)

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch,
                  self.search)

        sizer.Add(self.search, 0, wx.EXPAND, 0)

        self.book_list = KlipListCtrl(pnl_books,
                                      wx.ID_ANY,
                                      style=wx.LC_REPORT | wx.LC_NO_HEADER
                                      | wx.LC_HRULES | wx.LC_SINGLE_SEL)

        font = self.book_list.GetFont()
        font.PointSize += 5
        # font = font.Bold()
        self.book_list.SetFont(font)
        self.book_list.SetForegroundColour(wx.Colour(0x43, 0x43, 0x43))

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnBookSelected,
                  self.book_list)

        self._total_books = wx.StaticText(pnl_books,
                                          label="BOOKS (%d)" % 0,
                                          pos=(25, 25))

        sizer.Add(self._total_books, 0, wx.LEFT, 0)

        sizer.Add(self.book_list, 1, wx.EXPAND | wx.ALL, 0)

        pnl_books.SetSizer(sizer)

        # init right panel, show clippings.
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.book_title = wx.StaticText(pnl_clips, label='')

        font = self.book_title.GetFont()
        font.PointSize += 10
        font.Bold()
        self.book_title.SetFont(font)
        self.book_title.SetForegroundColour(wx.Colour(0x25, 0x91, 0xff))

        sizer.Add(self.book_title, 0, wx.EXPAND, 0)

        self.clip_list = KlipListCtrl(pnl_clips,
                                      wx.ID_ANY,
                                      style=wx.LC_REPORT | wx.LC_NO_HEADER
                                      | wx.LC_HRULES | wx.LC_SINGLE_SEL)

        self.clip_list.InsertColumn(0, "Clip")

        books = self.fillBooks()

        sizer.Add(self.clip_list, 1, wx.EXPAND | wx.ALL, 0)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showClipDetail,
                  self.clip_list)

        pnl_clips.SetSizer(sizer)

        font = self.clip_list.GetFont()
        font.PointSize += 3
        self.clip_list.SetFont(font)

        width = self.clip_list.GetSize().GetWidth() * 0.5
        PDEBUG('Update Column Width: %d' % width)
        self.clip_list.SetColumnWidth(0, width)

        # create a menu bar
        self.makeMenuBar()

        if books > 0:
            self.book_list.Select(0)

    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        loadItem = fileMenu.Append(-1, "&Load...", "Load clippings...")

        cleanItem = fileMenu.Append(-1, "&Clean...", "Clean clippings...")

        fileMenu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)

        # Now a help menu for the about item
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnLoadFile, loadItem)
        self.Bind(wx.EVT_MENU, self.cleanRecords, cleanItem)
        self.Bind(wx.EVT_MENU, self.OnExit, exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def cleanRecords(self, event):
        """Close the frame, terminating the application."""
        total = self.model.cleanUpBooks()
        if total > 0:
            pass  # Add dialog??

    def OnLoadFile(self, event):
        """Load clips from file.."""

        (books, clips) = self.model.loadFile(getClipPath())
        if books > 0:
            self.fillBooks()
        if clips > 0 or books > 0:
            self.showClipsOfBook()

        wx.MessageBox("Loaded %d books with %d clips." % (books, clips))

    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("This is a wxPython Hello World sample",
                      "About Hello World 2", wx.OK | wx.ICON_INFORMATION)

    def OnCancelSearch(self, evt):
        PDEBUG('ENTER')
        self.showClipsOfBook()

    def OnSearch(self, evt):
        PDEBUG('ENTER')
        target = self.search.GetValue()
        args = target.split()
        if not args:
            PDEBUG('empty search target...')
            return

        it = self.model.searchClips(args)
        self.showClips('Result for "%s"' % target, it)
        pass

    def fillBooks(self):
        """Fill book list.
        """

        self.book_list.ClearAll()
        self.book_list.SetBackgroundColour(wx.Colour(0xf6, 0xf6, 0xf6))

        self.book_list.InsertColumn(0, "Book")
        # 0 will insert at the start of the list

        iter = self.model.getBooks()
        idx = 0
        while iter.next():
            self.book_list.InsertItem(idx, u"   %s" % (iter.book))
            idx += 1

        width = self.book_list.GetSize().GetWidth() * 0.5
        self.book_list.SetColumnWidth(0, width)
        self._total_books.SetLabel('BOOKS (%d)' % idx)
        return idx

    def OnBookSelected(self, event):
        """
        """
        book = event.GetText().strip()

        self.showClipsOfBook(book)
        pass

    def showClipsOfBook(self, book=None):
        """Show clips of book.
        """
        if book:
            self._book = book

        if self._book is None:
            PDEBUG('No book selected.')
            return

        PDEBUG('Book: %s', self._book)
        iter = self.model.getClipsByName(self._book)
        self.showClips(self._book, iter)
        pass

    def showClips(self, title, it):
        """Show contents in clip_lis.
        """
        self.book_title.SetLabel("  %s" % title)
        self.clip_list.DeleteAllItems()

        idx = 0
        while it.next():
            item = wx.ListItem()
            item.SetData(it.id)
            item.SetId(idx)
            item.SetText(u"    %s" % (it.content))
            self.clip_list.InsertItem(item)
            idx += 1

        pass

    def showClipDetail(self, event):

        self._cur_item = event.GetItem()
        id = self._cur_item.GetData()
        txt = self._cur_item.GetText()
        PDEBUG('ID: %d -- %s', id, txt)
        clip = self.model.getClipById(id)
        self.detailPanel.UpdateContent(clip)

        # TODO:  adjust position of detail window.
        # self.detailPanel.Position(wx.Point(0,0), wx.Size(0,0))
        self.detailPanel.Show(True)
        pass

    def updateClip(self, clip, text):
        if self.model.updateClip(clip, text):
            # update clip_list
            self._cur_item.SetText(clip.content)
        pass

    def dropClip(self, clip):
        if self.model.dropClip(clip):
            # update clip_list
            pass  # TODO: refresh clip list.
        pass

    def newClip(self, content, typ, date):
        self.model.newClip(self._book, content, typ, date)
        pass


def startGUI(controller):
    """
    """

    # Check wxversion.
    version = wx.version().split()[0]
    major = int(version.split('.')[0])
    if major < 4:
        print('Requires wx version > 4.0')
        return

    app = wx.App()
    frm = KlipFrame(controller)

    # Show it.
    frm.Show()

    app.MainLoop()

    pass
