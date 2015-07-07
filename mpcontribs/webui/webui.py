import json
from flask import Flask
from mpcontribs.io.mpfile import MPFile
from mpcontribs.rest import ContributionMongoAdapter
from mpcontribs.builders import MPContributionsBuilder
app = Flask('webui')

@app.route('/')
def index():
    contributor = 'Patrick Huck <phuck@lbl.gov>'
    mpfile = MPFile.from_file('test_files/atn_test_input.txt')
    cma = ContributionMongoAdapter()
    docs = cma.submit_contribution(mpfile, contributor)
    mcb = MPContributionsBuilder(docs)
    mcb.build(contributor)
    return '<html><body><pre><code>'+json.dumps(mcb.mat_coll, indent=4)+'</code></pre></body></html>'

if __name__ == '__main__':
    app.debug = True
    app.run()
