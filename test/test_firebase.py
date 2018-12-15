import unittest
from unittest.mock import patch

from shyr import firebase

class TestFirebase(unittest.TestCase):

  def test_sync_logsErrorForInvalidDirectory(self):
    with self.assertLogs(level='ERROR') as cm:
      firebase.sync('invalid')
      self.assertRegex(cm.output[0], 'invalid is not one of')
