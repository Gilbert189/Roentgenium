from collections.abc import MutableMapping


class InlineDict(MutableMapping):
    strict = False

    def __init__(self, store, key):
        self.store = store
        if type(key) is str:
            key = key.encode()
        elif type(key) is not bytes:
            raise TypeError("inline dicts only supports strings or bytes")
        self.key = key

    def __getitem__(self, key):
        if type(key) is str:
            key = key.encode()
        elif type(key) is not bytes:
            raise TypeError("inline dicts only supports strings or bytes")
        assert not (self.strict and "." in key), "Key contains a dot"
        return self.store[self.key + b"." + key]

    def __setitem__(self, key, value):
        if type(key) is str:
            key = key.encode()
        elif type(key) is not bytes:
            raise TypeError("inline dicts only supports strings or bytes")
        assert not (self.strict and "." in key), "Key contains a dot"
        self.store[self.key + b"." + key] = value

    def __delitem__(self, key):
        if type(key) is str:
            key = key.encode()
        elif type(key) is not bytes:
            raise TypeError("inline dicts only supports strings or bytes")
        assert not (self.strict and "." in key), "Key contains a dot"
        del self.store[self.key + b"." + key]

    def __iter__(self):
        search_for = self.key + b"."
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
