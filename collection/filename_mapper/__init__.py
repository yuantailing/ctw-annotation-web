from . import filename_mapper
import os

here = os.path.dirname(__file__)
mapper = filename_mapper.FilenameMapper(os.path.join(here, 'old2new.pickle'), os.path.join(here, 'new2old.pickle'))
