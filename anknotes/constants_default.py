import os
from datetime import timedelta, datetime

PATH = os.path.dirname(os.path.abspath(__file__))

class FOLDERS():
    ADDONS = os.path.dirname(PATH)
    EXTRA = os.path.join(PATH, 'extra')
    ANCILLARY = os.path.join(EXTRA, 'ancillary')
    GRAPHICS = os.path.join(EXTRA, 'graphics')
    LOGS = os.path.join(EXTRA, 'logs')
    DEVELOPER = os.path.join(EXTRA, 'dev')
    USER = os.path.join(EXTRA, 'user')


class FILES():
    class LOGS():
        class FDN():
            ANKI_ORPHANS = 'Find Deleted Notes\\'
            UNIMPORTED_EVERNOTE_NOTES = ANKI_ORPHANS + 'UnimportedEvernoteNotes'
            ANKI_TITLE_MISMATCHES = ANKI_ORPHANS + 'AnkiTitleMismatches'
            ANKNOTES_TITLE_MISMATCHES = ANKI_ORPHANS + 'AnknotesTitleMismatches'
            ANKNOTES_ORPHANS = ANKI_ORPHANS + 'AnknotesOrphans'
            ANKI_ORPHANS += 'AnkiOrphans'

        BASE_NAME = ''
        DEFAULT_NAME = 'anknotes'
        MAIN = DEFAULT_NAME
        ACTIVE = DEFAULT_NAME
        USE_CALLER_NAME = False
        ENABLED = ['*']
        DISABLED = ['finder*', 'args*', 'counter*', 'Dicts*']
        SEE_ALSO_DISABLED = [4,6]

    class ANCILLARY():
        TEMPLATE = os.path.join(FOLDERS.ANCILLARY, 'FrontTemplate.htm')
        CSS = u'_AviAnkiCSS.css'
        CSS_QMESSAGEBOX = os.path.join(FOLDERS.ANCILLARY, 'QMessageBox.css')
        ENML_DTD = os.path.join(FOLDERS.ANCILLARY, 'enml2.dtd')

    class SCRIPTS():
        VALIDATION = os.path.join(FOLDERS.ADDONS, 'anknotes_start_note_validation.py')
        FIND_DELETED_NOTES = os.path.join(FOLDERS.ADDONS, 'anknotes_start_find_deleted_notes.py')

    class GRAPHICS():
        class ICON():
            EVERNOTE_WEB = os.path.join(FOLDERS.GRAPHICS, u'evernote_web.ico')
            EVERNOTE_ARTCORE = os.path.join(FOLDERS.GRAPHICS, u'evernote_artcore.ico')
            TOMATO = os.path.join(FOLDERS.GRAPHICS, u'Tomato-icon.ico')

        class IMAGE():
            EVERNOTE_WEB = None
            EVERNOTE_ARTCORE = None

        IMAGE.EVERNOTE_WEB = ICON.EVERNOTE_WEB.replace('.ico', '.png')
        IMAGE.EVERNOTE_ARTCORE = ICON.EVERNOTE_ARTCORE.replace('.ico', '.png')

    class USER():
        TABLE_OF_CONTENTS_ENEX = os.path.join(FOLDERS.USER, "Table of Contents.enex")
        LAST_PROFILE_LOCATION = os.path.join(FOLDERS.USER, 'anki.profile')


class ANKNOTES():
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    CACHE_SEARCHES = False
    UPDATE_DB_ON_START = False

    class HOOKS():
        DB = True
        SEARCH = True

    class LXML():
        ENABLE_IN_ANKI = False

    class DEVELOPER_MODE:
        ENABLED = (os.path.isfile(os.path.join(FOLDERS.DEVELOPER, 'anknotes.developer')))
        AUTOMATED = ENABLED and (os.path.isfile(os.path.join(FOLDERS.DEVELOPER, 'anknotes.developer.automate')))
        AUTO_RELOAD_MODULES = True

    class HIERARCHY():
        ROOT_TITLES_BASE_QUERY = ""

    class FORMATTING():
        BANNER_MINIMUM = 80
        COUNTER_BANNER_MINIMUM = 40
        LINE_PADDING_HEADER = 31
        LINE_LENGTH_TOTAL = 191
        LINE_LENGTH = LINE_LENGTH_TOTAL - 2
        LIST_PAD = 25
        PROGRESS_SUMMARY_PAD = 31
        PPRINT_WIDTH = 80
        TIMESTAMP_PAD = '\t' * 6
        TIMESTAMP_PAD_LENGTH = len(TIMESTAMP_PAD.replace('\t', ' ' * 4))
        TEXT_LENGTH = LINE_LENGTH_TOTAL - TIMESTAMP_PAD_LENGTH


class MODELS():
    class TYPES():
        CLOZE = 1

    class OPTIONS():
        IMPORT_STYLES = True

    DEFAULT = 'evernote_note'
    REVERSIBLE = 'evernote_note_reversible'
    REVERSE_ONLY = 'evernote_note_reverse_only'
    CLOZE = 'evernote_note_cloze'


class TEMPLATES():
    DEFAULT = 'EvernoteReview'
    REVERSED = 'EvernoteReviewReversed'
    CLOZE = 'EvernoteReviewCloze'


class FIELDS():
    TITLE = 'Title'
    CONTENT = 'Content'
    SEE_ALSO = 'See_Also'
    TOC = 'TOC'
    OUTLINE = 'Outline'
    EXTRA = 'Extra'
    EVERNOTE_GUID = 'Evernote GUID'
    UPDATE_SEQUENCE_NUM = 'updateSequenceNum'
    EVERNOTE_GUID_PREFIX = 'evernote_guid='
    LIST = [TITLE, CONTENT, SEE_ALSO, EXTRA, TOC, OUTLINE,
            UPDATE_SEQUENCE_NUM]

    class ORD():
        EVERNOTE_GUID = 0

    ORD.CONTENT = LIST.index(CONTENT) + 1
    ORD.SEE_ALSO = LIST.index(SEE_ALSO) + 1


class DECKS():
    DEFAULT = "Evernote"
    TOC_SUFFIX = "::See Also::TOC"
    OUTLINE_SUFFIX = "::See Also::Outline"


class ANKI():
    PROFILE_NAME = ''
    NOTE_LIGHT_PROCESSING_INCLUDE_CSS_FORMATTING = False


class TAGS():
    TOC = '#TOC'
    TOC_AUTO = '#TOC.Auto'
    OUTLINE = '#Outline'
    OUTLINE_TESTABLE = '#Outline.Testable'
    REVERSIBLE = '#Reversible'
    REVERSE_ONLY = '#Reversible_Only'


class EVERNOTE():
    class IMPORT():
        class PAGING():
            # Note that Evernote's API documentation says not to run API calls to findNoteMetadata with any less than a 15 minute interval
            # Auto Paging is probably only useful in the first 24 hours, when API usage is unlimited, or when executing a search that is likely to have most of the notes up-to-date locally
            # To keep from overloading Evernote's servers, and flagging our API key, I recommend pausing 5-15 minutes in between searches, the higher the better.
            class RESTART():
                INTERVAL = None
                DELAY_MINIMUM_API_CALLS = 10
                INTERVAL_OVERRIDE = 60 * 5
                ENABLED = False

            INTERVAL = 60 * 15
            INTERVAL_SANDBOX = 60 * 5
            RESTART.INTERVAL = INTERVAL * 2

        INTERVAL = PAGING.INTERVAL * 4 / 3
        METADATA_RESULTS_LIMIT = 10000
        QUERY_LIMIT = 250  # Max returned by API is 250
        API_CALLS_LIMIT = 300

    class UPLOAD():
        ENABLED = True  # Set False if debugging note creation
        MAX = -1  # Set to -1 for unlimited
        RESTART_INTERVAL = 30  # In seconds

        class VALIDATION():
            ENABLED = True
            AUTOMATED = False

    class API():
        class RateLimitErrorHandling:
            IgnoreError, ToolTipError, AlertError = range(3)

        CONSUMER_KEY = "holycrepe"
        IS_SANDBOXED = False
        EDAM_RATE_LIMIT_ERROR_HANDLING = RateLimitErrorHandling.ToolTipError
        DEBUG_RAISE_ERRORS = False


class TABLES():
    SEE_ALSO = "anknotes_see_also"
    NOTE_VALIDATION_QUEUE = "anknotes_note_validation_queue"
    TOC_AUTO = u'anknotes_toc_auto'

    class EVERNOTE():
        NOTEBOOKS = "anknotes_evernote_notebooks"
        TAGS = "anknotes_evernote_tags"
        NOTES = u'anknotes_evernote_notes'
        NOTES_HISTORY = u'anknotes_evernote_notes_history'

class HEADINGS():
    TOP = "Summary|Definitions|Classifications|Types|Presentations|Organ Involvement|Age of Onset|Si/Sx|Sx|Signs|Triggers|MCC's|MCCs|Inheritance|Incidence|Prognosis|Derivations|Origins|Embryological Origins|Mechanisms|MOA|Pathophysiology|Indications|Examples|Causes|Causative Organisms|Risk Factors|Complications|Side Effects|Drug S/Es|Associated Conditions|A/w|Diagnosis|Dx|Physical Exam|Labs|Hemodynamic Parameters|Lab Findings|Imaging|Screening Tests|Confirmatory Tests|Xray|CT|MRI"
    BOTTOM = "Management|Work Up|Tx"
    NOT_REVERSIBLE = BOTTOM + "|Dx|Diagnosis"
