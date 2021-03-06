# -*- coding: utf-8 -*-
### Python Imports
import os
import re, sre_constants
import sys

try:
    from pysqlite2 import dbapi2 as sqlite
    is_pysqlite = True
except ImportError:
    from sqlite3 import dbapi2 as sqlite
    is_pysqlite = False


### Anknotes Shared Imports
from anknotes.imports import in_anki
from anknotes.shared import *
from anknotes import stopwatch

### Anknotes Main Imports
from anknotes import menu, settings

### Anki Imports
if ANKNOTES.HOOKS.SEARCH:
    from anki.find import Finder
    from aqt import browser
if ANKNOTES.HOOKS.DB:
    from anki.db import DB
from anki.hooks import wrap, addHook
from aqt.preferences import Preferences
from aqt import mw
from aqt.qt import Qt, QIcon, QTreeWidget, QTreeWidgetItem, QDesktopServices, QUrl
from anki.utils import ids2str, splitFields

def import_timer_toggle():
    title = "&Enable Auto Import On Profile Load"
    doAutoImport = mw.col.conf.get(
        SETTINGS.ANKNOTES_CHECKABLE_MENU_ITEMS_PREFIX + '_' + title.replace(' ', '_').replace('&', ''), False)
    if not doAutoImport:
        return
    lastImport = SETTINGS.EVERNOTE.LAST_IMPORT.fetch()
    importDelay = 0
    if lastImport:
        td = (datetime.now() - datetime.strptime(lastImport, ANKNOTES.DATE_FORMAT))
        minimum = timedelta(seconds=max(EVERNOTE.IMPORT.INTERVAL, 20 * 60))
        if td < minimum:
            importDelay = (minimum - td).total_seconds()
    if importDelay is 0:
        return menu.import_from_evernote()
    m, s = divmod(importDelay, 60)
    log("> Starting Auto Import, Triggered by Profile Load, in %d:%02d min" % (m, s))
    return create_timer(importDelay, menu.import_from_evernote)

def _findEdited((val, args)):
    try:
        days = int(val)
    except ValueError:
        return None
    return "c.mod > %d" % (time.time() - days * 86400)


def _findAnknotes((val, args)):
    tmr = stopwatch.Timer(label='finder\\findAnknotes', begin=False)
    log_banner("FINDANKNOTES SEARCH: " + val.upper().replace('_', ' '), tmr.label, append_newline=False, clear=False)
    if not hasattr(_findAnknotes, 'note_ids'):
        _findAnknotes.note_ids = {}
    if val == 'hierarchical' or val == 'hierarchical_alt' and (
            val not in _findAnknotes.note_ids or not ANKNOTES.CACHE_SEARCHES):
        tmr.reset()
        val_root = val.replace('hierarchical', 'root')
        val_child = val.replace('hierarchical', 'child')
        _findAnknotes((val_root, None), )
        _findAnknotes((val_child, None), )
        _findAnknotes.note_ids[val] = _findAnknotes.note_ids[val_root] + _findAnknotes.note_ids[val_child]
        write_file_contents("  > %s Search Complete: ".ljust(25) % val.upper().replace('_', ' ') + "%-5s --> %3d results" % (
            tmr.str_long, len(_findAnknotes.note_ids[val])), tmr.label)

    if not hasattr(_findAnknotes, 'queries'):
        _findAnknotes.queries = {
            'all':        get_evernote_model_ids(True),
            'sub':        'n.sfld like "%:%"',
            'root_alt':   "n.sfld NOT LIKE '%:%' AND ank.title LIKE n.sfld || ':%'",
            'child_alt':  "n.sfld LIKE '%%:%%' AND UPPER(SUBSTR(n.sfld, 0, INSTR(n.sfld, ':'))) IN (SELECT UPPER(title) FROM %s WHERE title NOT LIKE '%%:%%' AND tagNames LIKE '%%,%s,%%') " % (
                TABLES.EVERNOTE.NOTES, TAGS.TOC),
            'orphan_alt': "n.sfld LIKE '%%:%%' AND UPPER(SUBSTR(n.sfld, 0, INSTR(n.sfld, ':'))) NOT IN (SELECT UPPER(title) FROM %s WHERE title NOT LIKE '%%:%%' AND tagNames LIKE '%%,%s,%%') " % (
                TABLES.EVERNOTE.NOTES, TAGS.TOC)
        }

    if val not in _findAnknotes.note_ids or (not ANKNOTES.CACHE_SEARCHES and 'hierarchical' not in val):
        tmr.reset()
        if val == 'root':
            _findAnknotes.note_ids[val] = get_anknotes_root_notes_nids()
        elif val == 'child':
            _findAnknotes.note_ids[val] = get_anknotes_child_notes_nids()
        elif val == 'orphan':
            _findAnknotes.note_ids[val] = get_anknotes_orphan_notes_nids()
        elif val in _findAnknotes.queries:
            pred = _findAnknotes.queries[val]
            col = 'n.id'
            table = 'notes n'
            if 'ank.' in pred:
                col = 'DISTINCT ' + col
                table += ', %s ank' % TABLES.EVERNOTE.NOTES
            sql = 'select %s from %s where ' % (col, table) + pred
            _findAnknotes.note_ids[val] = ankDB().list(sql)
        else:
            return None
        write_file_contents("  > Cached %s Note IDs: ".ljust(25) % val + "%-5s --> %3d results" % (
            tmr.str_long, len(_findAnknotes.note_ids[val])), tmr.label)
    else:
        write_file_contents("  > Retrieving %3d %s Note IDs from Cache" % (len(_findAnknotes.note_ids[val]), val), tmr.label)
    log_blank(tmr.label)
    return "c.nid IN %s" % ids2str(_findAnknotes.note_ids[val])


class CallbackItem(QTreeWidgetItem):
    def __init__(self, root, name, onclick, oncollapse=None):
        QTreeWidgetItem.__init__(self, root, [name])
        self.onclick = onclick
        self.oncollapse = oncollapse


def anknotes_browser_get_icon(icon=None):
    if icon:
        return QIcon(":/icons/" + icon)
    if not hasattr(anknotes_browser_get_icon, 'default_icon'):
        from anknotes.graphics import icoEvernoteWeb
        anknotes_browser_get_icon.default_icon = icoEvernoteWeb
    return anknotes_browser_get_icon.default_icon


def anknotes_browser_add_treeitem(self, tree, name, cmd, icon=None, index=None, root=None):
    if root is None:
        root = tree
    def onclick(c=cmd): return self.setFilter(c)
    if index:
        widgetItem = QTreeWidgetItem([_(name)])
        widgetItem.onclick = onclick
        widgetItem.setIcon(0, anknotes_browser_get_icon(icon))
        root.insertTopLevelItem(index, widgetItem)
        return root, tree
    item = self.CallbackItem(tree, _(name), onclick)
    item.setIcon(0, anknotes_browser_get_icon(icon))
    return root, tree


def anknotes_browser_add_tree(self, tree, items, root=None, name=None, icon=None):
    if root is None:
        root = tree
    for item in items:
        if isinstance(item[1], list):
            new_name = item[0]
            # write_file_contents('Tree: Name: %s: \n' % str(new_name) + repr(item))
            new_tree = self.CallbackItem(tree, _(new_name), None)
            new_tree.setExpanded(True)
            new_tree.setIcon(0, anknotes_browser_get_icon(icon))
            root = anknotes_browser_add_tree(self, new_tree, item[1], root, new_name, icon)
        else:
            # write_file_contents('Tree Item: Name: %s: \n' % str(name) + repr(item))
            root, tree = anknotes_browser_add_treeitem(self, tree, *item, root=root)
    return root


def anknotes_browser_tagtree_wrap(self, root, _old):
    """

    :param root:
    :type root : QTreeWidget
    :param _old:
    :return:
    """
    root = _old(self, root)
    indices = root.findItems(_("Added Today"), Qt.MatchFixedString)
    index = (root.indexOfTopLevelItem(indices[0]) + 1) if indices else 3
    tags = \
        [
            ["Edited This Week", "edited:7", "view-pim-calendar.png", index],
            ["Anknotes",
             [
                 ["All Anknotes", "anknotes:all"],
                 ["Hierarchy",
                  [
                      ["All Hierarchical Notes", "anknotes:hierarchical"],
                      ["Root Notes", "anknotes:root"],
                      ["Sub Notes", "anknotes:sub"],
                      ["Child Notes", "anknotes:child"],
                      ["Orphan Notes", "anknotes:orphan"]
                  ]
                  ],
                 # ["Hierarchy: Alt",
                 # [
                 # ["All Hierarchical Notes", "anknotes:hierarchical_alt"],
                 # ["Root Notes", "anknotes:root_alt"],
                 # ["Child Notes", "anknotes:child_alt"],
                 # ["Orphan Notes", "anknotes:orphan_alt"]
                 # ]
                 # ],
                 ["Front Cards", "card:1"]
             ]
             ]
        ]

    return anknotes_browser_add_tree(self, root, tags)


def anknotes_finder_findCards_wrap(self, query, order=False, _old=None):
    tmr = stopwatch.Timer(label='finder\\findCards')
    log_banner("FINDCARDS SEARCH: " + query, tmr.label, append_newline=False, clear=False)
    tokens = self._tokenize(query)
    preds, args = self._where(tokens)
    write_file_contents('Tokens: '.ljust(25) + ', '.join(tokens), tmr.label)
    if args:
        write_file_contents('Args: '.ljust(25) + ', '.join(tokens), tmr.label)
    if preds is None:
        write_file_contents('Preds: '.ljust(25) + '<NONE>', tmr.label)
        log_blank(tmr.label)
        return []

    order, rev = self._order(order)
    sql = self._query(preds, order)
    try:
        res = self.col.db.list(sql, *args)
    except Exception as ex:
        # invalid grouping
        log_error("Error with findCards Query %s: %s.\n%s" % (query, str(ex), [sql, args]), crosspost=tmr.label)
        return []
    if rev:
        res.reverse()
    write_file_contents("FINDCARDS DONE: ".ljust(25) + "%-5s --> %3d results" % (tmr.str_long, len(res)), tmr.label)
    log_blank(tmr.label)
    return res
    return _old(self, query, order)


def anknotes_finder_query_wrap(self, preds=None, order=None, _old=None):
    if _old is None or not isinstance(self, Finder):
        log_dump([self, preds, order], 'Finder Query Wrap Error', 'finder\\error', crosspost_to_default=False)
        return
    sql = _old(self, preds, order)
    if "ank." in preds:
        sql = sql.replace("select c.id", "select distinct c.id").replace("from cards c",
                                                                         "from cards c, %s ank" % TABLES.EVERNOTE.NOTES)
        write_file_contents('Custom anknotes finder SELECT query: \n%s' % sql, 'finder\\ank-query')
    elif TABLES.EVERNOTE.NOTES in preds:
        write_file_contents('Custom anknotes finder alternate query: \n%s' % sql, 'finder\\ank-query')
    else:
        write_file_contents("Anki finder query: %s" % sql[:100], 'finder\\query')
    return sql


def anknotes_search_hook(search):
    anknotes_search = {'edited': _findEdited, 'anknotes': _findAnknotes}
    for key, value in anknotes_search.items():
        if key not in search:
            search[key] = anknotes_search[key]

def reset_everything(upload=True):
    show_tooltip_enabled = show_tooltip.enabled if hasattr(show_tooltip, 'enabled') else None
    show_tooltip.enabled = False
    ankDB().InitSeeAlso(True)
    menu.resync_with_local_db()
    menu.see_also(upload=upload)
    show_tooltip.enabled = show_tooltip_enabled


def anknotes_profile_loaded():
    # write_file_contents('%s: anknotes_profile_loaded' % __name__, 'load')
    last_profile_dir = os.path.dirname(FILES.USER.LAST_PROFILE_LOCATION)
    if not os.path.exists(last_profile_dir):
        os.makedirs(last_profile_dir)
    with open(FILES.USER.LAST_PROFILE_LOCATION, 'w+') as myFile:
        print>> myFile, mw.pm.name,
    # write_file_contents('%s: anknotes_profile_loaded: menu.anknotes_load_menu_settings' % __name__, 'load')
    menu.anknotes_load_menu_settings()
    if EVERNOTE.UPLOAD.VALIDATION.ENABLED and EVERNOTE.UPLOAD.VALIDATION.AUTOMATED:
        # write_file_contents('%s: anknotes_profile_loaded: menu.upload_validated_notes' % __name__, 'load')
        menu.upload_validated_notes(True)
    if ANKNOTES.UPDATE_DB_ON_START:
        # write_file_contents('%s: anknotes_profile_loaded: update_anknotes_nids' % __name__, 'load')
        update_anknotes_nids()
    # write_file_contents('%s: anknotes_profile_loaded: import_timer_toggle' % __name__, 'load')
    import_timer_toggle()
    if ANKNOTES.DEVELOPER_MODE.AUTOMATED:
        '''
         For testing purposes only!
         Add a function here and it will automatically run on profile load
         You must create the files 'anknotes.developer' and 'anknotes.developer.automate' in the /extra/dev/ folder
        '''
        # write_file_contents('%s: anknotes_profile_loaded: ANKNOTES.DEVELOPER_MODE.AUTOMATED' % __name__, 'load')
        # menu.lxml_test()
        # menu.see_also([8])
        # menu.see_also(upload=False)
        reset_everything(False)
        # menu.see_also(set(range(0,10)) - {3,4,8})
        # ankDB().InitSeeAlso(True)
        # menu.resync_with_local_db()
        # menu.see_also([1, 2, 6, 7, 9])
        # menu.lxml_test()
        # menu.see_also()
        # reset_everything()
        # menu.import_from_evernote(auto_page_callback=lambda: lambda: menu.see_also(3))
        # mw.progress.timer(20000, lambda : menu.find_deleted_notes(True), False)
        pass

def anknotes_scalar(self, *a, **kw):
    log_text = 'Call to DB.scalar():'
    if not isinstance(self, DB):
        log_text += '\n   - Self:       ' + pf(self)
    if a:
        log_text += '\n   - Args:       ' + pf(a)
    if kw:
        log_text += '\n   - KWArgs:     ' + pf(kw)
    last_query='<None>'
    if hasattr(self, 'ank_lastquery'):
        last_query = self.ank_lastquery
        if is_str_type(last_query):
            last_query = last_query[:50]
        else:
            last_query = pf(last_query)
        log_text += '\n   - Last Query: ' + last_query
    write_file_contents(log_text + '\n', 'sql\\scalar')
    try:
        res = self.execute(*a, **kw)
    except TypeError as e:
        write_file_contents(" > ERROR with scalar while executing query: %s\n >  LAST QUERY: %s" % (str(e), last_query), 'sql\\scalar', crosspost='sql\\scalar-error')
        raise
    if not isinstance(res, sqlite.Cursor):
        write_file_contents(' > Cursor: %s' % pf(res), 'sql\\scalar')
    try:
        res = res.fetchone()
    except TypeError as e:
        write_file_contents(" > ERROR with scalar while fetching result: %s\n >  LAST QUERY: %s" % (str(e), last_query), 'sql\\scalar', crosspost='sql\\scalar-error')
        raise
    write_file_contents('', 'sql\\scalar')
    if res:
        return res[0]
    return None

def anknotes_execute(self, sql, *a, **kw):
    log_text = 'Call to DB.execute():'
    if not isinstance(self, DB):
        log_text += '\n   - Self:       ' + pf(self)
    if a:
        log_text += '\n   - Args:       ' + pf(a)
    if kw:
        log_text += '\n   - KWArgs:     ' + pf(kw)
    last_query=sql
    if is_str_type(last_query):
        last_query = last_query[:50]
    else:
        last_query = pf(last_query)
    log_text += '\n   - Query:     ' + last_query
    write_file_contents(log_text + '\n\n', 'sql\\execute')
    self.ank_lastquery = sql

def anknotes_onload():
    # write_file_contents('%s: anknotes_onload' % __name__, 'load')
    if in_anki():
        addHook("profileLoaded", anknotes_profile_loaded)
        if ANKNOTES.HOOKS.DB:
            DB.scalar = anknotes_scalar # wrap(DB.scalar, anknotes_scalar, "before")
            DB.execute = wrap(DB.execute, anknotes_execute, "before")
        if ANKNOTES.HOOKS.SEARCH:
            addHook("search", anknotes_search_hook)
            Finder._query = wrap(Finder._query, anknotes_finder_query_wrap, "around")
            Finder.findCards = wrap(Finder.findCards, anknotes_finder_findCards_wrap, "around")
            browser.Browser._systemTagTree = wrap(browser.Browser._systemTagTree, anknotes_browser_tagtree_wrap, "around")
        # write_file_contents('%s: anknotes_onload: anknotes_setup_menu' % __name__, 'load')
        menu.anknotes_setup_menu()
        Preferences.setupOptions = wrap(Preferences.setupOptions, settings.setup_evernote)
    # write_file_contents('%s: anknotes_onload: complete' % __name__, 'load')

anknotes_onload()