import pickle
import os

here = os.path.dirname(__file__)

class FilenameMapper:
    def __init__(self, old2new_filename, new2old_filename):
        try:
            fp = open(old2new_filename, 'rb')
            self.old2new = pickle.loads(fp.read())
            fp.close()
            fp = open(new2old_filename, 'rb')
            self.new2old = pickle.loads(fp.read())
            fp.close()
        except Exception as e:
            self.old2new, self.new2old = FilenameMapper.create_filename_map(old2new_filename, new2old_filename)

    @staticmethod
    def create_filename_map(old2new_filename, new2old_filename):
        list_filenames = ['list_nosign.txt', 'list_nosign_s.txt', 'list_sign.txt', 'list_sign_s.txt']
        s = set()
        for filename in list_filenames:
            with open(os.path.join(here, filename), 'r') as fp:
                for line in fp:
                    s.add(line.strip().split('.')[0])
        v = list(s)
        v.sort()
        old2new = {}
        new2old = {}
        for i in xrange(0, len(v)):
            name_new = '%06d' % (i + 1)
            old2new[v[i]] = [name_new]
            new2old[name_new] = v[i]
        with open(old2new_filename, 'wb') as fp:
            fp.write(pickle.dumps(old2new))
        with open(new2old_filename, 'wb') as fp:
            fp.write(pickle.dumps(new2old))
        return (old2new, new2old)

def main():
    pass

if __name__ == "__main__":
    main()
