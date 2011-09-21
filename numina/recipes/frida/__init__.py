
__all__ = ['find_recipe']

# equivalence
_equiv = {'bias': 'recipe1',
        'dark': 'recipe3',
        'direct_image': 'recipe4',
        'mosaic': 'recipe2'}

def find_recipe(mode):
    return _equiv[mode]

