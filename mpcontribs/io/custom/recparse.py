
import re
from mpcontribs.config import indent_symbol, csv_comment_char, mp_level01_titles
from .utils import get_indentor
from ..core.recdict import RecursiveDict
from ..core.utils import pandas_to_dict, nest_dict, normalize_root_level
from ..core.utils import strip_converter, read_csv
from collections import OrderedDict

class RecursiveParser():
    def __init__(self):
        self.section_titles = []
        self.document = RecursiveDict({})
        self.level = -1 # level counter

    def separator_regex(self):
        """get separator regex for section depth/level"""
        # (?:  ) => non-capturing group
        # (?:^|\n+) => match beginning of string OR one or more newlines
        # %s\s+ => match next-level separator followed by one or more spaces
        #    require minimum one space after section level identifier
        # (.+) => capturing group of one or more arbitrary characters
        # (?:$|\n*?) => match end-of-string OR zero or more newlines
        #    be non-greedy with newlines at end of string
        return r'(?:^|\n+)%s\s+(.+)(?:$|\n*?)' % get_indentor(self.level+1)

    def clean_title(self, title):
        """strip in-line comments & spaces, make lower-case if mp-id"""
        title = re.split(
            r'%s*' % csv_comment_char, title
        )[0].strip()
        if self.level+1 == 0:
            return normalize_root_level(title)
        return False, title

    def is_bare_section(self, title):
        """determine whether currently in bare section"""
        return (title != mp_level01_titles[0] and self.level == 0)

    def is_data_section(self, body):
        """determine whether currently in data section"""
        return (get_indentor() not in body and ':' not in body)

    def increase_level(self, next_title, is_general=False):
        """increase and prepare for next section level"""
        if is_general: self.section_titles.append(mp_level01_titles[0])
        self.section_titles.append(next_title)
        self.level += 1

    def reduce_level(self, is_general=False):
        """reduce section level"""
        self.level -= 1
        self.section_titles.pop()
        if is_general: self.section_titles.pop()

    def parse(self, file_string):
        """recursively parse sections according to number of separators"""
        # split into section title line (even) and section body (odd entries)
        sections = re.split(self.separator_regex(), file_string)
        if len(sections) > 1:
            # check for preceding bare section_body (without section title), and parse
            if sections[0]: self.parse(sections[0])
            # drop preceding bare section_body
            sections = sections[1:] # https://docs.python.org/2/library/re.html#re.split
            for section_index,section_body in enumerate(sections[1::2]):
                is_general, clean_title = self.clean_title(sections[2*section_index])
                self.increase_level(clean_title, is_general)
                self.parse(section_body)
                self.reduce_level(is_general)
        else:
            # separator level not found, convert section body to pandas object,
            section_title = self.section_titles[-1]
            is_data_section = self.is_data_section(file_string)
            pd_obj = read_csv(file_string, is_data_section=is_data_section)
            # TODO: include validation
            # add data section title to nest 'bare' data under data section
            # => artificially increase and decrease level (see below)
            is_bare_data = (is_data_section and self.is_bare_section(section_title))
            if is_bare_data: self.increase_level(mp_level01_titles[1])
            # mark data section with special 'data ' prefix
            if is_data_section and not \
               self.section_titles[-1].startswith(mp_level01_titles[1]):
                self.section_titles[-1] = ' '.join([
                    mp_level01_titles[1], self.section_titles[-1]
                ])
            # make default plot for each table, first column as x-column
            if is_data_section:
                self.document.rec_update(nest_dict(
                    {'x': pd_obj.columns[0], 'table': self.section_titles[-1]},
                    [self.section_titles[0], mp_level01_titles[2],
                     'default {}'.format(self.section_titles[-1])]
                ))
            # update nested dict/document based on section level
            self.document.rec_update(nest_dict(
                pandas_to_dict(pd_obj), self.section_titles
            ))
            if is_bare_data: self.reduce_level()
