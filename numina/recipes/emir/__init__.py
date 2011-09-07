
__all__ = ['find_recipe']

# equivalence
_equiv = {'mode1': 'recipe1',
    'mode2': 'recipe2'}

def find_recipe(mode):
    return _equiv[mode]

