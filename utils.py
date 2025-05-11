from collections.abc import MutableMapping


class InlineDict(MutableMapping):
    strict = False

    def __init__(self, store, key):
        self.store = store
        self.key = key

    def __getitem__(self, key):
        assert not (self.strict and "." in key), "Key contains a dot"
        return self.store[self.key + "." + key]

    def __setitem__(self, key, value):
        assert not (self.strict and "." in key), "Key contains a dot"
        self.store[self.key + "." + key] = value

    def __delitem__(self, key):
        assert not (self.strict and "." in key), "Key contains a dot"
        del self.store[self.key + "." + key]

    def __iter__(self):
        search_for = self.key + "."
        return (
            k[len(search_for):]
            for k in self.store.keys()
            if k.startswith(search_for)
        )

    def __len__(self):
        length = 0
        for _ in self:
            length += 1
        return length
