__author__ = "Gareth Coles"


class Yielder(object):
    data = None
    done = False

    def next(self):
        if self.done:
            raise StopIteration

        if self.data:
            self.done = True
            return self.data

        return None

    __next__ = next  # Python 3. Because I can.

    def write(self, data):
        # This will only work if you're using compatible data-types.
        self.data += data

    def close(self):
        if not self.done:
            self.done = True

        return self.done

    def __iter__(self):
        return self
