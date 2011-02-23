"""This module will get W0406 warning for importing self,
which should be ignored in Cheesecake score.
"""

__revision__ = 'satisfy pylint checker'

import import_self

print import_self.__revision__ # use imported module
