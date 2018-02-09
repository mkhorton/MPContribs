
import six, archieml, warnings, textwrap
from mpcontribs.config import mp_level01_titles, symprec, replacements
from mpcontribs.io.core.mpfile import MPFileCore
from mpcontribs.io.core.recdict import RecursiveDict
from mpcontribs.io.core.utils import nest_dict, normalize_root_level
from mpcontribs.io.core.utils import read_csv, make_pair
from mpcontribs.io.core.components import Table
from pandas import MultiIndex

class MPFile(MPFileCore):
    """Object for representing a MP Contribution File in ArchieML format."""

    @staticmethod
    def from_string(data):
        # use archieml-python parse to import data
        rdct = RecursiveDict(archieml.loads(data))
        rdct.rec_update()
        # post-process internal representation of file contents
        for key in list(rdct.keys()):
            is_general, root_key = normalize_root_level(key)
            if is_general:
                # make part of shared (meta-)data, i.e. nest under `general` at
                # the beginning of the MPFile
                if mp_level01_titles[0] not in rdct:
                    rdct.insert_before(
                        list(rdct.keys())[0],
                        (mp_level01_titles[0], RecursiveDict())
                    )
                rdct.rec_update(nest_dict(
                    rdct.pop(key), [ mp_level01_titles[0], root_key ]
                ))
            else:
                # normalize identifier key (pop & insert)
                # using rec_update since we're looping over all entries
                # also: support data in bare tables (marked-up only by
                #       root-level identifier) by nesting under 'data'
                value = rdct.pop(key)
                keys = [ root_key ]
                if isinstance(value, list): keys.append('table')
                rdct.rec_update(nest_dict(value, keys))
                # Note: CSV section is marked with 'data ' prefix during iterate()
                for k,v in rdct[root_key].iterate():
                    if isinstance(k, six.string_types) and \
                       k.startswith(mp_level01_titles[1]):
                        # k = table name (incl. data prefix)
                        # v = csv string from ArchieML free-form arrays
                        table_name = k[len(mp_level01_titles[1]+'_'):]
                        pd_obj = read_csv(v)
                        rdct[root_key].pop(table_name)
                        rdct[root_key].rec_update(nest_dict(
                            pd_obj.to_dict(), [k]
                        ))
                        rdct[root_key].insert_default_plot_options(pd_obj, k)
                # convert CIF strings into pymatgen structures
                if mp_level01_titles[3] in rdct[root_key]:
                    from pymatgen.io.cif import CifParser
                    for name in list(rdct[root_key][mp_level01_titles[3]].keys()):
                        cif = rdct[root_key][mp_level01_titles[3]].pop(name)
                        parser = CifParser.from_string(cif)
                        structure = parser.get_structures(primitive=False)[0]
                        rdct[root_key][mp_level01_titles[3]].rec_update(nest_dict(
                            structure.as_dict(), [name]
                        ))
        return MPFile.from_dict(rdct)

    def get_string(self):
        from pymatgen import Structure
        lines, scope = [], []
        table_start = mp_level01_titles[1]+'_'
        for key,value in self.document.iterate():
            if isinstance(value, Table):
                header = any([bool(
                    isinstance(col, str) or isinstance(col, str)
                ) for col in value])
                if isinstance(value.index, MultiIndex):
                    value.reset_index(inplace=True)
                csv_string = value.to_csv(
                    index=False, header=header, float_format='%g', encoding='utf-8'
                )[:-1]
                lines += csv_string.decode('utf-8').split('\n')
            elif isinstance(value, Structure):
                from pymatgen.io.cif import CifWriter
                cif = CifWriter(value, symprec=symprec).__str__()
                lines.append(make_pair(
                    ''.join([replacements.get(c, c) for c in key]), cif+':end'
                ))
            else:
                level, key = key
                key = key if isinstance(key, str) else key.decode('utf-8')
                # truncate scope
                level_reduction = bool(level < len(scope))
                if level_reduction: del scope[level:]
                # append scope and set delimiters
                if value is None:
                    is_table = key.startswith(table_start)
                    if is_table:
                        # account for 'data_' prefix
                        key = key[len(table_start):]
                        start, end = '\n[+', ']'
                    else:
                        start, end = '\n{', '}'
                    scope.append(
                        ''.join([replacements.get(c, c) for c in key])
                    )
                # correct scope to omit internal 'general' section
                scope_corr = scope
                if scope[0] == mp_level01_titles[0]:
                    scope_corr = scope[1:]
                # insert scope line
                if (value is None and scope_corr)or \
                   (value is not None and level_reduction):
                    lines.append(start+'.'.join(scope_corr)+end)
                # insert key-value line
                if value is not None:
                    val = str(value) if not isinstance(value, str) else value
                    value_lines = [val] if val.startswith('http') \
                            else textwrap.wrap(val)
                    if len(value_lines) > 1:
                        value_lines = [''] + value_lines + [':end']
                    lines.append(make_pair(
                        ''.join([replacements.get(c, c) for c in key]),
                        '\n'.join(value_lines)
                    ))
        return '\n'.join(lines) + '\n'

MPFileCore.register(MPFile)
