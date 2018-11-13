import re

import wl_data as wl
from util import *

class Matcher:

    def __init__(self, matcher, match_when_used):
        split_matches = re.findall('^([^\[]+)(\[\s*(.*)\])?$', matcher) # split the object matcher and the list of method matchers
        if len(split_matches) != 1:
            raise RuntimeError(
                'Failed to parse structure of matcher, ' +
                'should be in the form \'object_matcher\' or \'object_matcher[list_of_message_matchers]\'')
        obj_matcher = split_matches[0][0] # the object portion
        self._parse_obj_matcher(obj_matcher)
        message_matchers = split_matches[0][1] # the list of message matchers, can be an empty string
        self.messages = None
        if message_matchers:
            self.messages = re.findall('[\w\*]+', message_matchers)
        self.match_when_used = match_when_used

    def _parse_obj_matcher(self, matcher):
        id_matches = re.findall('(^|[^\w\.-])(\d+)(\.(\d+))?', matcher)
        obj_id = None
        obj_generation = None
        if id_matches:
            if len(id_matches) > 1:
                raise RuntimeError(
                    'Found multiple object IDs (' +
                    ', '.join(i[1] + ('.' + i[3] if i[3] else '') for i in id_matches) +
                    ')')
            obj_id = int(id_matches[0][1])
            if id_matches[0][3]:
                obj_generation = int(id_matches[0][3])
        obj_name_matches = re.findall('([a-zA-Z\*][\w\*-]*)', matcher)
        self.type = None
        if obj_name_matches:
            if len(obj_name_matches) > 1:
                raise RuntimeError(
                    'Found multiple object type names (' +
                    ', '.join(i for i in obj_name_matches) +
                    ')')
            self.type = obj_name_matches[0]
        self.obj = None
        self.obj_id = None # Only set if self.obj is None
        self.obj_generation = None # Only set if self.obj is None
        if obj_id:
            try:
                if obj_generation:
                    self.obj = wl.Object.look_up_specific(obj_id, obj_generation, self.type)
                else:
                    self.obj = wl.Object.look_up_most_recent(obj_id, self.type)
            except AssertionError as e:
                self.obj_id = obj_id
                self.obj_generation = obj_generation

    def _matches_obj(self, obj):
        if self.obj:
            return obj == self.obj
        else:
            if self.obj_id and self.obj_id != obj.id:
                return False
            elif self.obj_generation and self.obj_generation != obj.generation:
                return False
            elif self.type and not str_matches(self.type, obj.type):
                return False
            else:
                return True

    def _matches_message(self, message):
        if not self._matches_obj(message.obj):
            if not self.match_when_used:
                return False
            found_match = False
            for i in message.used_objects():
                if self._matches_obj(i):
                    found_match = True
                    break
            if not found_match:
                return False
        if self.messages == None:
            return True
        for i in self.messages:
            if str_matches(i, message.name):
                return True
        return False

    def matches(self, item):
        if isinstance(item, wl.Object):
            return _matches_obj(item)
        elif isinstance(item, wl.Message):
            return self._matches_message(item)
        else:
            raise TypeError()

class Collection:
    def __init__(self, matchers, is_whitelist):
        self.matchers = []
        self.is_whitelist = is_whitelist
        for i in re.findall('([^\s;:,\[\]]+(\s*\[([^\]]*)\])?)', matchers):
            try:
                self.matchers.append(Matcher(i[0], is_whitelist))
            except RuntimeError as e:
                warning('Failed to parse \'' + i[0] + '\': ' + str(e))

    def matches(self, item):
        found = False
        for i in self.matchers:
            if i.matches(item):
                found = True
        return found == self.is_whitelist

    def match_none_matcher():
        return Collection('', True)

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)