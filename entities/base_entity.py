class BaseEntity:
    def __init__(self, onto_desc, scene=None):
        self.onto_description = onto_desc
        self.name = onto_desc.get('data', {}).get('label', {}).get('value')
        self.uri = 'UNKNOWN_URI'
        self.scene = scene
        self.is_deleting = False
