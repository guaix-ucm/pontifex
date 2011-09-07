
import importlib

def find_recipe(instrument, mode):
    base = 'numina.recipes.%s' % instrument
    try:
        mod = importlib.import_module(base)
    except ImportError:
        msg = 'No instrument %s' % instrument
        raise ValueError(msg)

    try:
        repmod = mod.find_recipe(mode)
    except KeyError:
        msg = 'No recipe for mode %s' % mode
        raise ValueError(msg)
        
    return '%s.%s' % (base, repmod)

def find_parameters(recipe_name):
    # query somewhere for the precomputed parameters
    return {}
