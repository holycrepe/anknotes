# -*- coding: utf-8 -*-
# Python Imports
from subprocess import *

try:
    from pysqlite2 import dbapi2 as sqlite
except ImportError:
    from sqlite3 import dbapi2 as sqlite

# Anknotes Shared Imports
from anknotes.shared import *
from anknotes.constants import *

# Anknotes Main Imports
from anknotes.Controller import Controller

# Anki Imports
from aqt.qt import SIGNAL, QMenu, QAction
from aqt import mw
from aqt.utils import getText
from anki.storage import Collection

DEBUG_RAISE_API_ERRORS = False


# noinspection PyTypeChecker
def anknotes_setup_menu():
    menu_items = [
        [u"&Anknotes",
         [
             ["&Import from Evernote", import_from_evernote],
             ["&Enable Auto Import On Profile Load", {'action': anknotes_menu_auto_import_changed, 'checkable': True}],
             ["Note &Validation",
              [
                  ["Validate &And Upload Pending Notes", lambda: validate_pending_notes],
                  ["SEPARATOR", None],
                  ["&Validate Pending Notes", lambda: validate_pending_notes(True, False)],
                  ["&Upload Validated Notes", upload_validated_notes]
              ]
              ],
             ["Process &See Also Links [Power Users Only!]",
              [
                  ["Complete All &Steps", see_also],
                  ["SEPARATOR", None],
                  ["Step &1: Process Notes Without See Also Field", lambda: see_also(1)],
                  ["Step &2: Extract Links from TOC", lambda: see_also(2)],
                  ["Step &3: Create Auto TOC Evernote Notes", lambda: see_also(3)],
                  ["Step &4: Validate and Upload Auto TOC Notes", lambda: see_also(4)],
                  ["SEPARATOR", None],
                  ["Step &5: Insert TOC/Outline Links Into Evernote Notes", lambda: see_also(5)],
                  ["Step &6: Validate and Upload Modified Notes", lambda: see_also(6)],
                  ["SEPARATOR", None],
                  ["Step &7: Insert TOC and Outline Content Into Anki Notes", lambda: see_also(7)]
              ]
              ],
             ["&Maintenance Tasks",
              [
                  ["Find &Deleted Notes", find_deleted_notes],
                  ["Res&ync with Local DB", resync_with_local_db],
                  ["Update Evernote &Ancillary Data", update_ancillary_data]
              ]
             ]

         ]
         ]
    ]
    add_menu_items(menu_items)


def add_menu_items(menu_items, parent=None):
    if not parent: parent = mw.form.menubar
    for title, action in menu_items:
        if title == "SEPARATOR":
            parent.addSeparator()
        elif isinstance(action, list):
            menu = QMenu(_(title), parent)
            parent.insertMenu(mw.form.menuTools.menuAction(), menu)
            add_menu_items(action, menu)
        else:
            checkable = False
            if isinstance(action, dict):
                options = action
                action = options['action']
                if 'checkable' in options:
                    checkable = options['checkable']
            menu_action = QAction(_(title), mw, checkable=checkable)
            parent.addAction(menu_action)
            parent.connect(menu_action, SIGNAL("triggered()"), action)
            if checkable:
                anknotes_checkable_menu_items[title] = menu_action


def anknotes_menu_auto_import_changed():
    title = "&Enable Auto Import On Profile Load"
    doAutoImport = anknotes_checkable_menu_items[title].isChecked()
    mw.col.conf[
        SETTINGS.ANKNOTES_CHECKABLE_MENU_ITEMS_PREFIX + '_' + title.replace(' ', '_').replace('&', '')] = doAutoImport
    mw.col.setMod()
    mw.col.save()
    # import_timer_toggle()


def anknotes_load_menu_settings():
    global anknotes_checkable_menu_items
    for title, menu_action in anknotes_checkable_menu_items.items():
        menu_action.setChecked(mw.col.conf.get(
            SETTINGS.ANKNOTES_CHECKABLE_MENU_ITEMS_PREFIX + '_' + title.replace(' ', '_').replace('&', ''), False))


def import_from_evernote_manual_metadata(guids=None):
    if not guids:
        guids = find_evernote_guids(file(ANKNOTES.FOLDER_LOGS + 'anknotes-Find Deleted Notes\\MissingFromAnki.log', 'r').read())
    showInfo("Manually downloading %n Notes: \n%s" % (len(guids), str(guids)))
    controller = Controller()
    controller.evernote.initialize_note_store()
    controller.forceAutoPage = True
    controller.currentPage = 1
    controller.ManualGUIDs = guids
    controller.proceed()

def import_from_evernote(auto_page_callback=None):
    controller = Controller()
    controller.evernote.initialize_note_store()
    controller.auto_page_callback = auto_page_callback
    if auto_page_callback:
        controller.forceAutoPage = True
        controller.currentPage = 1
    else:
        controller.forceAutoPage = False
        controller.currentPage = mw.col.conf.get(SETTINGS.EVERNOTE_PAGINATION_CURRENT_PAGE, 1)
    controller.proceed()


def upload_validated_notes(automated=False):
    controller = Controller()
    controller.upload_validated_notes(automated)

def find_deleted_notes():
    showInfo("""In order for this to work, you must create a 'Table of Contents' Note using the Evernote desktop application. Include all notes that you want to sync with Anki.

Export this note to the following path: '%s'.

Press Okay to save and close your Anki collection, open the command-line deleted notes detection tool, and then re-open your Anki collection.

Once the command line tool is done running, you will get a summary of the results, and will be prompted to delete Anki Orphan Notes or download Missing Evernote Notes""" % ANKNOTES.TABLE_OF_CONTENTS_ENEX)

    mw.col.close()
    handle = Popen(ANKNOTES.FIND_DELETED_NOTES_SCRIPT, stdin=PIPE, stderr=PIPE, stdout=PIPE, shell=True)
    stdoutdata, stderrdata = handle.communicate()
    info = ("ERROR: {%s}\n\n" % stderrdata) if stderrdata else ''
    info += "Return data: \n%s" % stdoutdata
    showInfo(info)
    dels = file(os.path.join(ANKNOTES.FOLDER_LOGS, ANKNOTES.LOG_BASE_NAME + '-Find Deleted Notes\\MissingFromEvernote.log'), 'r').read()
    guids = find_evernote_guids(dels)
    count = len(guids)
    mfile = os.path.join(ANKNOTES.FOLDER_LOGS, ANKNOTES.LOG_BASE_NAME + '-Find Deleted Notes\\MissingFromAnki.log')
    missing = file(mfile, 'r').read()
    missing_guids = find_evernote_guids(missing)
    count_missing = len(missing_guids)

    showInfo("Completed: %s\n\n%s" + ('Press Okay and we will show you a prompt to confirm deletion of the %d orphan Anki notes' % count) if count > 0 else 'No Orpan Anki Notes Found', info[:1000])
    mw.col.reopen()
    mw.col.load()
    if count > 0:
        code = getText("Please enter code 'ANKI_DEL_%d' to delete your orphan Anki note(s)" % count)[0]
        if code is 'ANKI_DEL_%d' % count:
            ankDB().executemany("DELETE FROM %s WHERE guid = ?" % TABLES.EVERNOTE.NOTES, [[x] for x in guids])
            ankDB().commit()
            show_tooltip("Deleted all %d Orphan Anki Notes" % count, time_out=5000)
    if count_missing > 0:
        ret = showInfo("Would you like to import %d missing Evernote Notes?\n\n<a href='%s'>Click to view results</a>" % mfile, cancelButton=True, richText=True)
        if ret:
            show_tooltip("YES !")
            # import_from_evernote_manual_metadata()
        else:
            show_tooltip("NO  !")





def validate_pending_notes(showAlerts=True, uploadAfterValidation=True):
    if showAlerts:
        showInfo("""Press Okay to save and close your Anki collection, open the command-line note validation tool, and then re-open your Anki collection.%s

Anki will be unresponsive until the validation tool completes. This will take at least 45 seconds.

The tool's output will be shown. If it is truncated, you may view the full log in the anknotes addon folder at extra\\logs\\anknotes-MakeNoteQueue-*.log"""
                 % ' Any validated notes will be automatically uploaded once your Anki collection is reopened.' if uploadAfterValidation else '')
    mw.col.close()
    # mw.closeAllCollectionWindows()
    handle = Popen(ANKNOTES.VALIDATION_SCRIPT, stdin=PIPE, stderr=PIPE, stdout=PIPE, shell=True)
    stdoutdata, stderrdata = handle.communicate()
    info = ("ERROR: {%s}\n\n" % stderrdata) if stderrdata else ''
    info += "Return data: \n%s" % stdoutdata
    if showAlerts: showInfo("Completed: %s\n\n%s" % ('Press Okay to begin uploading successfully validated notes to the Evernote Servers' if uploadAfterValidation else '', info[:1000]))

    mw.col.reopen()
    mw.col.load()

    if uploadAfterValidation:
        upload_validated_notes()


def see_also(steps=None):
    controller = Controller()
    if not steps: steps = range(1, 10)
    if isinstance(steps, int): steps = [steps]
    showAlerts = (len(steps) == 1)
    if 1 in steps:
        # Should be unnecessary once See Also algorithms are finalized
        log(" > See Also: Step 1: Processing Un Added See Also Notes")
        controller.process_unadded_see_also_notes()
    if 2 in steps:
        log(" > See Also: Step 2: Extracting Links from TOC")
        controller.anki.extract_links_from_toc()
    if 3 in steps:
        log(" > See Also: Step 3: Creating Auto TOC Evernote Notes")
        controller.create_auto_toc()
    if 4 in steps:
        log(" > See Also: Step 4: Validate and Upload Auto TOC Notes")
        validate_pending_notes(showAlerts)
    if 5 in steps:
        log(" > See Also: Step 5: Inserting TOC/Outline Links Into Evernote Notes")
        controller.anki.insert_toc_into_see_also()
    if 6 in steps:
        log(" > See Also: Step 6: Validate and Upload Modified Notes")
        validate_pending_notes(showAlerts)
    if 7 in steps:
        log(" > See Also: Step 7: Inserting TOC/Outline Contents Into Anki Notes")
        controller.anki.insert_toc_and_outline_contents_into_notes()


def update_ancillary_data():
    controller = Controller()
    controller.evernote.initialize_note_store()
    controller.update_ancillary_data()


def resync_with_local_db():
    controller = Controller()
    controller.resync_with_local_db()


anknotes_checkable_menu_items = {}
