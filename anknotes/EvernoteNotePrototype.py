from anknotes.EvernoteNoteTitle import EvernoteNoteTitle
from anknotes.html import generate_evernote_url, generate_evernote_link, generate_evernote_link_by_level
from anknotes.structs import upperFirst, EvernoteAPIStatus
from anknotes.logging import log, log_blank, log_error

class EvernoteNotePrototype:
    ################## CLASS Note ################
    Title = None
    """:type: EvernoteNoteTitle"""
    Content = ""
    Guid = ""
    UpdateSequenceNum = -1
    """:type: int"""
    TagNames = []
    TagGuids = []
    NotebookGuid = ""
    Status = EvernoteAPIStatus.Uninitialized
    """:type : EvernoteAPIStatus """
    Children = []

    @property
    def Tags(self):
        return self.TagNames

    def process_tags(self):
        if isinstance(self.TagNames, str) or isinstance(self.TagNames, unicode):
            self.TagNames = self.TagNames[1:-1].split(',')
        if isinstance(self.TagGuids, str) or isinstance(self.TagGuids, unicode):
            self.TagGuids = self.TagGuids[1:-1].split(',')

    def __repr__(self):
        return u"<EN Note: %s: '%s'>" % (self.Guid, self.Title)

    def __init__(self, title=None, content=None, guid=None, tags=None, notebookGuid=None, updateSequenceNum=None,
                 whole_note=None, db_note=None):
        """

        :type whole_note: evernote.edam.type.ttypes.Note
        :type db_note: sqlite3.dbapi2.Row
        """

        self.Status = EvernoteAPIStatus.Uninitialized
        self.TagNames = tags
        if whole_note is not None:
            self.Title = EvernoteNoteTitle(whole_note)
            self.Content = whole_note.content
            self.Guid = whole_note.guid
            self.NotebookGuid = whole_note.notebookGuid
            self.UpdateSequenceNum = whole_note.updateSequenceNum
            self.Status = EvernoteAPIStatus.Success
            return
        if db_note is not None:
            self.Title = EvernoteNoteTitle(db_note)
            db_note_keys = db_note.keys()
            if isinstance(db_note['tagNames'], str):
                db_note['tagNames'] = unicode(db_note['tagNames'], 'utf-8')
            for key in ['content', 'guid', 'notebookGuid', 'updateSequenceNum', 'tagNames', 'tagGuids']:
                if not key in db_note_keys:
                    log_error("FATAL ERROR: Unable to find key %s in db note %s! \n%s" % (key, self.Title.FullTitle, db_note_keys))
                    log("Values: \n\n" + str({k: db_note[k] for k in db_note_keys  }), 'EvernoteNotePrototypeInit')
                else:
                    setattr(self, upperFirst(key), db_note[key])
            if isinstance(self.Content, str):
                self.Content = unicode(self.Content, 'utf-8')
            self.process_tags()
            self.Status = EvernoteAPIStatus.Success
            return
        self.Title = EvernoteNoteTitle(title)
        self.Content = content
        self.Guid = guid
        self.NotebookGuid = notebookGuid
        self.UpdateSequenceNum = updateSequenceNum
        self.Status = EvernoteAPIStatus.Manual

    def generateURL(self):
        return generate_evernote_url(self.Guid)

    def generateLink(self, value=None):
        return generate_evernote_link(self.Guid, self.Title.Name, value)

    def generateLevelLink(self, value=None):
        return generate_evernote_link_by_level(self.Guid, self.Title.Name, value)

    ### Shortcuts to EvernoteNoteTitle Properties; Autogenerated with regex /def +(\w+)\(\)\:/def \1\(\):\r\n\treturn self.Title.\1\r\n/ 
    @property
    def Level(self):
        return self.Title.Level

    @property
    def Depth(self):
        return self.Title.Depth

    @property
    def FullTitle(self):
        return self.Title.FullTitle

    @property
    def Name(self):
        return self.Title.Name

    @property
    def Root(self):
        return self.Title.Root

    @property
    def Base(self):
        return self.Title.Base

    @property
    def Parent(self):
        return self.Title.Parent

    @property
    def TitleParts(self):
        return self.Title.TitleParts

    @property
    def IsChild(self):
        return self.Title.IsChild

    @property
    def IsRoot(self):
        return self.Title.IsRoot

    @property
    def IsAboveLevel(self, level_check):
        return self.Title.IsAboveLevel(level_check)

    @property
    def IsBelowLevel(self, level_check):
        return self.Title.IsBelowLevel(level_check)

    @property
    def IsLevel(self, level_check):
        return self.Title.IsLevel(level_check)

        ################## END CLASS Note ################
