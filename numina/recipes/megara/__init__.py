
__all__ = ['find_recipe']

# equivalence
_equiv = {'bias': 'recipe1',
        'mosaic': 'recipe2'}

def find_recipe(mode):
    return _equiv[mode]

