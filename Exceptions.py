class ProjectException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return repr(self.name)
