from __future__ import unicode_literals, print_function
import six, archieml
from mpcontribs.config import mp_level01_titles
from ..core.mpfile import MPFileCore
from ..core.recdict import RecursiveDict
from ..core.utils import nest_dict, normalize_root_level
from ..core.utils import read_csv, pandas_to_dict

class MPFile(MPFileCore):
    """Object for representing a MP Contribution File in ArchieML format."""

    @staticmethod
    def from_string(data):
        # use archieml-python parse to import data
        mpfile = MPFile.from_dict(RecursiveDict(archieml.loads(data)))
        # save original file to be extended for get_string
        mpfile.string = data
        # post-process internal representation of file contents
        for key in mpfile.document.keys():
            is_general, root_key = normalize_root_level(key)
            if is_general:
                # make part of shared (meta-)data, i.e. nest under `general` at
                # the beginning of the MPFile
                if mp_level01_titles[0] not in mpfile.document:
                    mpfile.document.insert_before(
                        mpfile.document.keys()[0],
                        (mp_level01_titles[0], RecursiveDict())
                    )
                mpfile.document.rec_update(nest_dict(
                    mpfile.document.pop(key),
                    [ mp_level01_titles[0], root_key ]
                ))
            else:
                # normalize identifier key (pop & insert)
                # using rec_update since we're looping over all entries
                mpfile.document.rec_update(nest_dict(
                    mpfile.document.pop(key), [ root_key ]
                ))
                for k,v in mpfile.document[root_key].iterate():
                    if isinstance(k, six.string_types) and k.startswith('csv--'):
                        # v = csv string from ArchieML free-from arrays
                        table_name = k.split('--')[1]
                        mpfile.document[root_key].pop(table_name)
                        mpfile.document[root_key].rec_update(nest_dict(
                            pandas_to_dict(read_csv(v)), [table_name]
                        ))
        # - support bare (marked-up only by root-level identifier) data tables by nesting under 'data'
        # - mark data section with 'data ' prefix in level-1 key, also for table name in root-level 'plots'
        # - make default plot (add entry in 'plots') for each table, first column as x-column
        # - update data (free-form arrays) section of original dict/document parsed by ArchieML
        return mpfile

    def get_string(self):
        raise NotImplementedError('TODO')

MPFileCore.register(MPFile)