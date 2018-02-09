
import os, re
from tempfile import gettempdir

indent_symbol = '>'
min_separator_length = 3 # minimum separator length to avoid collision w/ '>>'
mp_categories = {
    'mp_id': [
        'numerify', 'mp-####'
    ], # mp-id, e.g. mp-1234
    'composition': [
        'numerify', 'A#B#'
    ], # composition, e.g. A2B3
    'chemical_system': [
        'lexify', '??'
    ], # chem. system, e.g. AB
}
mp_level01_titles = [ '_hdata', '_tdata', '_gdata', '_structures' ]
csv_comment_char = '#'
csv_database = os.path.join(
  os.path.dirname(os.path.realpath(__file__)),
  '../test_files/lahman-csv_2014-02-14'
)
mp_id_pattern = re.compile('^(mp|por|mvc)-\d+(?:--\d+)?$', re.IGNORECASE)
object_id_pattern = re.compile('^[a-f\d]{24}$')
default_mpfile_path = os.path.join(gettempdir(), 'mpfile.txt')
symprec = 1e-10
replacements = {' ': '_', '[': '', ']': '', '{': '', '}': '', ':': '_'}
