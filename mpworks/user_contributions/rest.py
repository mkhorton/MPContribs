import os

def submit_snl_from_cif(submitter_email, cif_file, metadata_file):
    """submit StructureNL via CIF and YAML MetaData files

    method to submit StructureNL object generated from CIF file via separate
    file containing MetaData in YAML format as required by the MPStructureNL
    constructor. Developed to be used for the submission of new structures
    during RSC publishing process (pilot project).

    Args:
    metadata_file: name of file parsed via monty's loadfn
    """
    from mpworks.submission.submission_mongo import SubmissionMongoAdapter
    from monty.serialization import loadfn
    from pymatgen.core import Structure
    from pymatgen.matproj.snl import StructureNL
    sma = SubmissionMongoAdapter.auto_load()
    pth = os.path.dirname(os.path.realpath(__file__))
    structure = Structure.from_file(os.path.join(pth, cif_file))
    config = loadfn(os.path.join(pth, metadata_file))
    if not config['references'].startswith('@'):
        config['references'] = open(
            os.path.join(pth, config['references']),'r'
        ).read()
    snl = StructureNL(structure, **config)
    sma.submit_snl(snl, submitter_email)


from pymongo import MongoClient
from monty.serialization import loadfn

def create_db(host='localhost', port=27019, db_name='user_contributions'):
    """create database and add user for testing"""
    client = MongoClient(host, port, j=True)
    client.drop_database(db_name)
    client[db_name].add_user('test', 'test', read_only=False)

def init_materials_collection(
    host='localhost', port=27019, db_name='user_contributions',
    username='test', password='test'
):
    """init a test materials collection from official 'dtu' materials"""
    config = loadfn(os.path.join(os.environ['DB_LOC'], 'materials_db.yaml'))
    rclient = MongoClient(config['host'], config['port'], j=True)
    rclient[config['db']].authenticate(config['username'], config['password'])
    wclient = MongoClient(host, port, j=True)
    wclient[db_name].authenticate(username, password)
    rmaterials = rclient[config['db']].materials
    wmaterials = wclient[db_name].materials
    wmaterials.remove()
    for doc in rmaterials.find(
      {'external_data':{'$exists':'dtu'}},
      {'external_data.dtu': 0}
    ):
        wmaterials.insert(doc)
    print wmaterials.count(), ' materials inserted'

from parsers import RecursiveParser
import datetime
from StringIO import StringIO
from config import mp_level01_titles
from faker import Faker

class ContributionMongoAdapter(object):
    """adapter/interface for user contributions"""
    def __init__(self, db_yaml='materials_db_dev.yaml'):
        config = loadfn(os.path.join(os.environ['DB_LOC'], db_yaml))
        client = MongoClient(config['host'], config['port'], j=False)
        client[config['db']].authenticate(
            config['username'], config['password']
        )
        self.id_assigner = client[config['db']].contribution_id_assigner
        self.contributions = client[config['db']].contributions
        self.materials = client[config['db']].materials
        self.fake = Faker()
        self.available_mp_ids = []
        for doc in self.materials.aggregate([
            { '$project': { 'task_id': 1, '_id': 0 } },
            { '$match':  { 'task_id': { '$regex': '^mp-[0-9]{1}$' } } },
        ], cursor={}):
            self.available_mp_ids.append(doc['task_id'])

    def _reset(self):
        """reset all collections"""
        self.contributions.remove()
        self.id_assigner.remove()
        self.id_assigner.insert({'next_contribution_id': 1})

    def _get_next_contribution_id(self):
        """get the next contribution id"""
        return self.id_assigner.find_and_modify(
            update={'$inc': {'next_contribution_id': 1}}
        )['next_contribution_id']

    def submit_contribution(
        self, input_handle, contributor_email, contribution_id=None,
        parser=RecursiveParser()
    ):
        """submit user data to `materials.contributions` collection

        Args:
        input_handle: object to "connect" to input, i.e. file handle
        contribution_id: None if new contribution else update/replace
        parser: parser class to use on input handle
        """
        if isinstance(input_handle, file):
            fileExt = os.path.splitext(input_handle.name)[1][1:]
            parser.init(fileExt=fileExt)
            parser.parse(input_handle.read())
        elif isinstance(input_handle, StringIO):
            parser.init()
            parser.parse(input_handle.getvalue())
        else:
            raise TypeError(
                'type %r not supported as input handle!' % type(input_handle)
            )
        # TODO: implement update/replace based on contribution_id=None
        # apply general level-0 section on all other level-0 sections if existent
        general_title = mp_level01_titles[0]
        if general_title in parser.document:
            general_data = parser.document.pop(general_title)
            for k in parser.document:
                parser.document[k][general_title] = general_data
        # treat every mp_cat_id as separate database insert
        contribution_ids = []
        for k,v in parser.document.iteritems():
            #mp_cat_id = k.split('--')[0]
            mp_cat_id = self.fake.random_element(elements=self.available_mp_ids)
            doc = {
                'contributor_email': contributor_email,
                'contribution_id': self._get_next_contribution_id(),
                'contributed_at': datetime.datetime.utcnow().isoformat(),
                'mp_cat_id': mp_cat_id, 'content': v
            }
            self.contributions.insert(doc)
            contribution_ids.append(doc['contribution_id'])
        return contribution_ids

    def fake_multiple_contributions(self, num_contributions=20):
        """fake the submission of many contributions"""
        from fakers.mp_csv.v1 import MPCsvFile
        for n in range(num_contributions):
            f = MPCsvFile(usable=True, main_general=self.fake.pybool())
            csv = f.make_file()
            contributor = '%s <%s>' % (self.fake.name(), self.fake.email())
            print self.submit_contribution(csv, contributor)
