"""This module provides the views for the portal."""

import os
from importlib import import_module
from django.shortcuts import render_to_response
from django.template import RequestContext
from mpcontribs.users_modules import *
from mpcontribs.rest.views import get_endpoint

def index(request):
    ctx = RequestContext(request)
    if request.user.is_authenticated():
        a_tags = [[], []]
        for mod_path in get_users_modules():
            explorer = os.path.join(mod_path, 'explorer', 'apps.py')
            if os.path.exists(explorer):
                entry = {
                    'name': get_user_explorer_name(explorer),
                    'title': os.path.basename(mod_path).replace('_', ' ')
                }
                mod_path_split = mod_path.split(os.sep)
                rester_path_split = mod_path_split[-4:] + ['rest', 'rester']
                rester_path = os.path.join(*rester_path_split)
                rester_path += '.py'
                idx = 1
                if os.path.exists(rester_path):
                    m = import_module('.'.join(rester_path_split[1:]))
                    UserRester = getattr(m, get_user_rester(mod_path_split[-1]))
                    endpoint = request.build_absolute_uri(get_endpoint())
                    r = UserRester(request.user.api_key, endpoint=endpoint)
                    idx = int(not r.released)
                a_tags[idx].append(entry)
    else:
        ctx.update({'alert': 'Please log in!'})
    return render_to_response("mpcontribs_portal_index.html", locals(), ctx)
