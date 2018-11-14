"""
@licence: Apache 2.0
@Copyright (c) 2018, Christine Staiger (SURFsara)
@author: Christine Staiger
@author: Stefan Wolfsheimer
"""
import importlib
import imp
import sys
import os


def module_name_of_draft(s):
    return s.lower()


def module_exists(module_name):
    try:
        imp.find_module(module_name)
        return True
    except ImportError:
        return False


def get_draft_class(draft, search_paths):
    draft_module = module_name_of_draft(draft)
    dirname = os.path.dirname(__file__)
    default_path = os.path.join(dirname, "drafts")
    real_sp = []
    for sp in search_paths:
        searchp = os.path.abspath(sp.format(iBridges=dirname))
        real_sp.append(searchp)
        if searchp == default_path:
            if(module_exists(draft_module)):
                mod = importlib.import_module(draft_module)
                if hasattr(mod, draft):
                    return getattr(mod, draft)

        else:
            searchp = os.path.abspath(sp.format(iBridges=dirname))
            real_sp.append(searchp)
            sys.path.insert(0, searchp)
            if(module_exists(draft_module)):
                mod = importlib.import_module(draft_module)
                if hasattr(mod, draft):
                    return getattr(mod, draft)
    msg = "could not find module {0} in search paths: {1}".format(
        draft_module,
        " ".join(real_sp))
    raise ImportError(msg)
