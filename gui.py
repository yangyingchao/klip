#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import wx.lib.mixins.listctrl as listmix
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
from common import getClipPath, PDEBUG


class KlipListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class KlipDetailWindow(wx.PopupWindow):
    """Adds a bit of text and mouse movement to the wx.PopupWindow"""

    def __init__(self, parent, style):
        wx.PopupWindow.__init__(self, parent, style)

        self.eom = ExpandoTextCtrl(self, size=(600, -1),
                                   value="This control will expand as you type")

        self.eom.SetMaxHeight(600)
        self.Bind(EVT_ETC_LAYOUT_NEEDED, self.OnRefit, self.eom)

        font = self.eom.GetFont()
        font.PointSize += 5
        self.eom.SetFont(font)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.eom, 1, wx.EXPAND | wx.ALL, 10)

        # type
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, "type     "),
                0, wx.LEFT | wx.RIGHT, 10)

        self.st_type = wx.StaticText(self, -1, "")
        row.Add(self.st_type, 0, wx.LEFT | wx.RIGHT, 10)
        self.sizer.Add(row, 0, wx.EXPAND | wx.ALL, 2)

        # location
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, "location"),
                0, wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, 10)

        self.st_location = wx.StaticText(self, -1, "")
        row.Add(self.st_location, 0, wx.LEFT | wx.RIGHT, 10)

        self.sizer.Add(row, 0, wx.EXPAND | wx.ALL, 2)

        # date
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, -1, "date     "),
                0, wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, 10)

        self.st_date = wx.StaticText(self, -1, "")
        row.Add(self.st_date, 0, wx.LEFT | wx.RIGHT, 10)
        self.sizer.Add(row, 0, wx.EXPAND | wx.ALL, 5)

        # done button
        btn_done = wx.Button(self, -1, 'Done')
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(btn_done, 0, wx.ALL, 10)
        btn_done.Bind(wx.EVT_BUTTON, self.OnDone)
        self.sizer.Add(row, 0, wx.EXPAND | wx.ALL, 0)

        self.SetSizerAndFit(self.sizer)

    def OnRefit(self, evt):
        # The Expando control will redo the layout of the
        # sizer it belongs to, but sometimes this may not be
        # enough, so it will send us this event so we can do any
        # other layout adjustments needed.  In this case we'll
        # just resize the frame to fit the new needs of the sizer.
        self.Fit()
        pass

    def OnDone(self, evt):
        """Hide this window..
        """
        PDEBUG('K: %s', evt)
        self.Show(False)
        pass

    def OnMouseLeftDown(self, evt):
        self.Refresh()
        self.ldPos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
        self.wPos = self.ClientToScreen((0, 0))
        self.pnl.CaptureMouse()

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            dPos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
            nPos = (self.wPos.x + (dPos.x - self.ldPos.x),
                    self.wPos.y + (dPos.y - self.ldPos.y))
            self.Move(nPos)

    def OnMouseLeftUp(self, evt):
        if self.pnl.HasCapture():
            self.pnl.ReleaseMouse()

    def OnRightUp(self, evt):
        self.Show(False)
        wx.CallAfter(self.Destroy)

    def UpdateContent(self, clip):
        PDEBUG('POS: %s, DATE: %s', clip.pos, clip.date)
        self.eom.SetValue(clip.content)

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

        self.detailPanel = KlipDetailWindow(self, wx.SIMPLE_BORDER)
        self.SetMinSize(wx.Size(800, 600))

        sp = wx.SplitterWindow(self, style=wx.SP_BORDER | wx.SP_3DBORDER)
        sp.SetSplitMode(wx.SPLIT_VERTICAL)
        self.detailPanel = KlipDetailWindow(self, wx.SIMPLE_BORDER)
        sp.SetMinimumPaneSize(50)

        # create a panel in the frame
        pnl_books = wx.Panel(sp)
        pnl_clips = wx.Panel(sp)
        pnl_clips.SetBackgroundColour(wx.Colour(255, 255, 255))

        sp.SplitVertically(pnl_books, pnl_clips, int(
            round(self.GetSize().GetWidth() * 0.3)))

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.search = wx.SearchCtrl(pnl_books, size=(
            200, -1), style=wx.TE_PROCESS_ENTER)
        self.search.ShowSearchButton(True)
        self.search.ShowCancelButton(True)

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch, self.search)

        sizer.Add(self.search,
                  0, wx.EXPAND, 0)

        self.book_list = KlipListCtrl(pnl_books,
                                      wx.ID_ANY,
                                      style=wx.LC_REPORT | wx.LC_NO_HEADER |
                                      wx.LC_HRULES | wx.LC_SINGLE_SEL)

        font = self.book_list.GetFont()
        font.PointSize += 5
        # font = font.Bold()
        self.book_list.SetFont(font)
        self.book_list.SetForegroundColour(wx.Colour(0x43, 0x43, 0x43))

        self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                  self.OnBookSelected, self.book_list)

        self._total_books = wx.StaticText(pnl_books, label="BOOKS (%d)" %
                                          0, pos=(25, 25))

        sizer.Add(self._total_books, 0, wx.LEFT, 0)

        sizer.Add(self.book_list, 1, wx.EXPAND | wx.ALL, 0)

        pnl_books.SetSizer(sizer)

        # init right panel, show clippings.
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.book_title = wx.StaticText(
            pnl_clips, label='')

        font = self.book_title.GetFont()
        font.PointSize += 10
        font.Bold()
        self.book_title.SetFont(font)
        self.book_title.SetForegroundColour(wx.Colour(0x25, 0x91, 0xff))

        sizer.Add(self.book_title,
                  0, wx.EXPAND, 0)

        self.clip_list = KlipListCtrl(pnl_clips,
                                      wx.ID_ANY,
                                      style=wx.LC_REPORT | wx.LC_NO_HEADER |
                                      wx.LC_HRULES | wx.LC_SINGLE_SEL)

        self.clip_list.InsertColumn(0, "Clip")

        books = self.fillBooks()

        sizer.Add(self.clip_list, 1, wx.EXPAND | wx.ALL, 0)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                  self.showClipDetail, self.clip_list)

        pnl_clips.SetSizer(sizer)

        font = self.clip_list.GetFont()
        font.PointSize += 3
        self.clip_list.SetFont(font)

        width = self.clip_list.GetSize().GetWidth()*0.5
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
        loadItem = fileMenu.Append(-1, "&Load...",
                                   "Load clippings...")

        cleanItem = fileMenu.Append(-1, "&Clean...",
                                    "Clean clippings...")

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
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
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
                      "About Hello World 2",
                      wx.OK | wx.ICON_INFORMATION)

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

        width = self.book_list.GetSize().GetWidth()*0.5
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

        item = event.GetItem()
        id = item.GetData()
        txt = item.GetText()
        PDEBUG('ID: %d -- %s', id, txt)
        clip = self.model.getClipById(id)
        self.detailPanel.UpdateContent(clip)

        # TODO:  adjust position of detail window.
        # self.detailPanel.Position(wx.Point(0,0), wx.Size(0,0))
        self.detailPanel.Show(True)
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
    self.detailPanel.UpdateContent(clip)

    app.MainLoop()

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
