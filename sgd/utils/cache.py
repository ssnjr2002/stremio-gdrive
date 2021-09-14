import json
import pickle


class Cache:
    def __init__(self, filename, filetype):
        self.filename = filename
        self.filetype = filetype
        self.bin = 'b' if filetype is pickle else ''
        try:
            self.load()
        except FileNotFoundError:
            self.contents = dict()
            self.save() 

    def load(self):
        with open(self.filename, f'r{self.bin}') as file_:
            self.contents = self.filetype.load(file_)
            print(f"Reading {self.filename}!")

    def save(self):
        with open(self.filename, f'w{self.bin}') as file_:
            self.filetype.dump(self.contents, file_)
            print(f"Writing to {self.filename}!")


class Pickle(Cache):
    def __init__(self, filename):
        super().__init__(filename, pickle)


class Json(Cache):
    def __init__(self, filename):
        super().__init__(filename, json)
