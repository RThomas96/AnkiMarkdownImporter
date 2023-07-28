import unittest
import logging

import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.resolve().parent.resolve()))

import geodeDatabase as geo

class DatabaseConstructor(unittest.TestCase):
    #Before each test
    def setUp(self):
        pass

    #After each test
    def tearDown(self):
        pass

    def check_singleFile(self, database):
        self.assertEqual(database.cardDatabase.iloc[0]['question'], 'Basic question ?')
        self.assertEqual(database.cardDatabase.iloc[0]['answer'], 'This is an answer.')
        self.assertEqual(database.cardDatabase.iloc[0]['tags'], [])

        self.assertEqual(database.cardDatabase.iloc[1]['question'], 'Basic question2 ?')
        self.assertEqual(database.cardDatabase.iloc[1]['answer'], 'This is an answer.\nWith two lines.')
        self.assertEqual(database.cardDatabase.iloc[1]['tags'], [])

        self.assertEqual(database.cardDatabase.iloc[2]['question'], 'Basic question3 ?')
        self.assertEqual(database.cardDatabase.iloc[2]['answer'], 'This is an answer.')
        self.assertEqual(database.cardDatabase.iloc[2]['tags'], ['CustomTag'])

    def test_singleFileConstructor(self):
        database = geo.Database("files/singleFile.md")
        self.assertTrue(len(database.cardDatabase.index) == 3)
        self.check_singleFile(database)

    def test_fileTreeConstructor(self):
        database = geo.Database("files/testFileTree")
        self.assertTrue(len(database.cardDatabase.index) == 5)
        self.check_singleFile(database)
        self.assertEqual(database.cardDatabase.iloc[3]['question'], 'Basic question4 ?')
        #self.assertEqual(database.cardDatabase.iloc[3]['answer'], 'This is an answer.')
        self.assertEqual(database.cardDatabase.iloc[3]['tags'], [])

    def test_writeAnkiCSV(self):
        database = geo.Database("files/testFileTree")
        database.writeAnkiCSV("AnkiCSVTest.csv")

    def test_writeAnkiCSV_onGeode(self):
        database = geo.Database()
        database.writeAnkiCSV("AnkiCSVTestGeode.csv")

    def test_parseLogseq(self):
        database = geo.Database("files/logseq_journal.md", format=geo.Format.Logseq)
        database.writeAnkiCSV("AnkiCSVTestLogseq.csv")

    def test_parseLogseqWriteMarkdown(self):
        database = geo.Database("files/logseq_journal.md", format=geo.Format.Logseq)
        database.writeMarkdown("TestLogseq.md")

if __name__ == '__main__':
    unittest.main(verbosity=2)
