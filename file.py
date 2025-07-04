class File():
    def __init__(self, filename='', body=[]):
        self.filename = filename
        self.body = body

    def body_as_string(self):
        return "".join(self.body)
