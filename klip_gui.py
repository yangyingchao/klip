#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import wx
import wx.html2
import wx.lib.mixins.listctrl as listmix
import markdown
import os
import sys
from wx.adv import TaskBarIcon as TaskBarIcon
from enum import Enum
from datetime import datetime
from klip_common import getClipPath, PDEBUG
from images import icons

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

    def __init__(self, parent):

        wx.PopupWindow.__init__(self, parent, wx.BORDER_THEME)

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
        text = self.editor.GetValue().strip()
        if len(text) == 0:
            self.Restore()
            return

        if self.state == State.Editting:
            self.editor.Show(False)
            self.parent.updateClip(self._clip, text)
        elif self.state == State.Creating:
            self.parent.newClip(text, self.st_type.GetLabel(),
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
            self.Show(False)
            self.parent.dropClip(self._clip)

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
        self._book_id = None
        self._search_target = None

        super(KlipFrame, self).__init__(None,
                                        size=wx.Size(1200, 760),
                                        title='Klip',
                                        name='Klip')
        # ensure the parent's __init__ is called

        icon = icons.klip.GetIcon()
        self.SetIcon(icon)

        self.tb = TaskBarIcon(wx.adv.TBI_DOCK)
        self.tb.SetIcon(icon)

        sp = wx.SplitterWindow(self, style=wx.SP_BORDER | wx.SP_3DBORDER)
        sp.SetSplitMode(wx.SPLIT_VERTICAL)
        sp.SetMinimumPaneSize(50)
        self.detailPanel = KlipDetailWindow(self)
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
        self.book_list.ClearAll()
        self.book_list.SetBackgroundColour(wx.Colour(0xf6, 0xf6, 0xf6))

        self.bl_width = self.book_list.GetSize().GetWidth() * 0.5

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
        sizer.Add(self.book_title, 0, wx.EXPAND, 10)

        self.book_info = wx.StaticText(pnl_clips, label='')

        font = self.book_info.GetFont()
        font.PointSize += 5
        font.Bold()
        self.book_info.SetFont(font)
        # self.book_info.SetForegroundColour(wx.Colour(0x25, 0x91, 0xff))

        sizer.Add(self.book_info, 0, wx.EXPAND, 10)

        self.clip_list = KlipListCtrl(pnl_clips,
                                      wx.ID_ANY,
                                      style=wx.LC_REPORT | wx.LC_NO_HEADER
                                      | wx.LC_HRULES | wx.LC_SINGLE_SEL)

        self.clip_list.InsertColumn(0, "Clip")

        # books = self.fillBooks()

        sizer.Add(self.clip_list, 1, wx.EXPAND | wx.ALL, 0)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showClipDetail,
                  self.clip_list)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnClipSelected,
                  self.clip_list)

        pnl_clips.SetSizer(sizer)

        font = self.clip_list.GetFont()
        font.PointSize += 3
        self.clip_list.SetFont(font)

        width = self.clip_list.GetSize().GetWidth() * 0.5
        PDEBUG('Update Column Width: %d' % width)
        self.clip_list.SetColumnWidth(0, width)

        self.clip_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,
                            self.OnRightClickClips)

        self.refreshContents()

        # create a menu bar
        self.makeMenuBar()

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

        self.refreshContents()

    def refreshContents(self):
        """
        """
        self.fillBooks()
        total_books = self.book_list.GetItemCount()
        PDEBUG('BOOK_ID: %s, total: %s', self._book_id, total_books)
        if self._book_id is None:
            self.book_list.Select(0)
        elif self._book_id >= total_books:
            self.book_list.Select(total_books - 1)
        else:
            self.book_list.Select(self._book_id)
        pass

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

        self.book_list.DeleteAllItems()

        self.book_list.InsertColumn(0, "Book")
        # 0 will insert at the start of the list

        iter = self.model.getBooks()
        idx = 0
        while iter.next():
            item = wx.ListItem()
            item.SetData(iter.id)
            item.SetId(idx)
            item.SetText(u"    %s" % (iter.name))
            self.book_list.InsertItem(item)
            idx += 1

        self._total_books.SetLabel('BOOKS (%d)' % idx)
        self.book_list.SetColumnWidth(0, self.bl_width)

        return idx

    def OnBookSelected(self, event):
        """
        """
        self._book_id = event.GetItem().GetData()
        PDEBUG('BOOK_ID: %d', self._book_id)
        self.showClipsOfBook()
        self._clip = None
        pass

    def OnClipSelected(self, event):
        self._cur_item = event.GetItem()
        id = self._cur_item.GetData()
        txt = self._cur_item.GetText()
        PDEBUG('ID: %d -- %s', id, txt)
        self._clip = self.model.getClipById(id)
        PDEBUG('CLIP: %s', self._clip)
        pass

    def OnRightClickClips(self, evt):
        """
        """
        PDEBUG('enter: %s', evt)

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewIdRef()
            self.popupID2 = wx.NewIdRef()
            self.popupID3 = wx.NewIdRef()
            self.popupID5 = wx.NewIdRef()
            self.popupID6 = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.OnNew, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnEdit, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnDelete, id=self.popupID3)

        # make a menu
        menu = wx.Menu()
        # add some items
        menu.Append(self.popupID1, "New Clip")
        menu.Append(self.popupID2, "Edit Selected")
        menu.Append(self.popupID3, "Delete Selected")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)

        menu.Destroy()

        pass

    def OnNew(self, evt):
        """
        """
        self.detailPanel.Show(True)
        self.detailPanel.OnNew(evt)
        pass

    def OnEdit(self, evt):
        """
        """
        PDEBUG('NOT IMPLEMENT.')
        self.detailPanel.Show(True)
        self.detailPanel.OnNew(evt)

        pass

    def OnDelete(self, evt):
        PDEBUG('NOT IMPLEMENT.')
        if self._clip is None:
            PDEBUG('oops')

        self.dropClip(self._clip)
        self._clip = None

    def showClipsOfBook(self):
        """Show clips of book.
        """

        PDEBUG('BOOK_ID: %d', self._book_id)

        book_iter = self.model.getBookById(self._book_id)
        if not book_iter.next():
            print('Failed to load book info, book_id: %d' % (self._book_id))
            sys.exit(1)

        book = book_iter.name
        author = book_iter.author

        iter = self.model.getClipsByBookId(self._book_id)
        self.showClips(book, author, iter)
        pass

    def showClips(self, title, author, it):
        """Show contents in clip_li.s
        """
        self.book_title.SetLabel("  %s -- %s" % (title, author))
        self.clip_list.DeleteAllItems()

        idx = 0
        while it.next():
            item = wx.ListItem()
            item.SetData(it.id)
            item.SetId(idx)
            item.SetText(u"    %s" % (it.content))
            self.clip_list.InsertItem(item)
            idx += 1

        self.book_info.SetLabel('      Total clips: %d' % idx)

        pass

    def showClipDetail(self, event):

        self._cur_item = event.GetItem()
        id = self._cur_item.GetData()
        clip = self.model.getClipById(id)
        self.detailPanel.UpdateContent(clip)

        # TODO:  adjust position of detail window.
        # self.detailPanel.Position(wx.Point(0,0), wx.Size(0,0))
        self.detailPanel.Show(True)
        pass

    def updateClip(self, clip, text):
        self.model.updateClip(clip, text)
        self.clip_list.SetItemText(self._cur_item.GetId(), u"    %s" % text)
        pass

    def dropClip(self, clip):
        idx = self._cur_item.GetId()
        PDEBUG('DELETE IDX: %d', idx)
        self.model.dropClip(clip)
        self.clip_list.DeleteItem(idx)
        if idx < self.clip_list.GetItemCount():
            self.clip_list.Select(idx)

        self.Refresh()
        self.clip_list.SetFocus()

        # If there are no clips left for current book, ask if we should remove
        # current book...
        if self.clip_list.GetItemCount() == 0:
            self.refreshContents()
        pass

    def newClip(self, content, typ, date):
        self.model.newClip(self._book, content, typ, date)
        self.showClipsOfBook()

        pass


class KlipApp(wx.App):
    """Klip Application.
    """

    def OnInit(self):
        """
        """
        wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName("Klip")

        return True


def startGUI(controller):
    """
    """

    # Check wxversion.
    version = wx.version().split()[0]
    major = int(version.split('.')[0])
    if major < 4:
        print('Requires wx version > 4.0')
        return

    app = KlipApp()
    frm = KlipFrame(controller)

    # Show it.
    frm.Show()

    app.MainLoop()

    pass
