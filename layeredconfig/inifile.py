import os
import logging
from six.moves import configparser
from six import text_type as str
try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    # if on python 2.6
    from ordereddict import OrderedDict

from . import ConfigSource

class INIFile(ConfigSource):
    def __init__(self,
                 inifilename=None,
                 writable=True, 
                 defaultsection="__root__",
                 *args,
                 **kwargs):
        """
        :param inifile: The name of a ini-style configuration file. The
                        file should have a top-level section named
                        __root__, whose keys are turned into top-level
                        configuration parameters. Any other sections in
                        this file are turned into nested config
                        objects.
        :type inifile: str
        """
        super(INIFile, self).__init__(*args, **kwargs)
        if inifilename:
            if not os.path.exists(inifilename):
                logging.warn("INI file %s does not exist" % inifilename)
                self.source = None
                self.inifilename = None
            else:
                self.source = configparser.ConfigParser(dict_type=OrderedDict)
                self.source.read(inifilename)
                self.inifilename = inifilename
        # only used when creating new INIFile objects internally
        elif 'config' in kwargs:  
            self.source = kwargs['config']
            self.inifilename = None
        else:
            # This is an "empty" INIFile object
            self.inifilename = None
        if 'section' in kwargs:
            self.sectionkey = kwargs['section']
        else:
            self.sectionkey = defaultsection
            self.dirty = False
        self.writable = writable
        self.defaultsection = defaultsection

    def typed(self, key):
        # INI files carry no intrinsic type information
        return False

    def subsections(self):
        # self.source may be None if we provided the path to a
        # nonexistent inifile (this should probably throw an exception
        # instead)
        if not self.source:
            return []
        elif self.sectionkey != self.defaultsection:
            # sections can't be nested using configparser
            return []
        else:
            return [x for x in self.source.sections() if x != self.defaultsection]

    def subsection(self, key):
        return INIFile(config=self.source, section=key,
                       parent=self, identifier=self.identifier)

    def has(self, key):
        return key in self.source.options(self.sectionkey)
        
    def get(self, key):
        return str(self.source.get(self.sectionkey, key))

    def set(self, key, value):
        # Note: We need to stringify all values
        self.source.set(self.sectionkey, key, str(value))
        self.dirty = False

    def keys(self):
        if self.source:
            for k in self.source.options(self.sectionkey):
                yield k

    def save(self):
        # this should only be called on root objects
        assert not self.parent, "save() should only be called on root objects"
        if self.inifilename:
            with open(self.inifilename, "w") as fp:
                self.source.write(fp)