""" Extract and manage data from a file tree organized by the Geode convention.

Extract cards from a single Markdown file or a file tree organized by the Geode convention 
and generate a Pandas dataframe. Cards can be written in various formats like Anki compatible
CSV format or plain Markdown format.
Uses `FileParser` to extract cards from each file according to its format.

Handled formats:
    - Markdown: read/write
    - Logseq markdown: read
    - Anki CSV: write

Typical usage example:

  database = Database()
  database.writeAnkiCSV("path/to/my/file.csv")
"""
import os
import pandas as pd
import ntpath
import pathlib
from collections import namedtuple

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension

from card import Card
from fileParser import FileParser, Format

class Database:
    """ Extract cards from a path and write them to various formats."""
    def __init__(self, path="/home/thomas/note/geode/cards", format=Format.MDGeode):
        """ Populate `cardDatabase` with the cards extracted from `path`.

        Args:
            path: The path to a single file or a directory. If path is a directory is passed all files 
                with `.md` extension are parsed.
            format: The format needs to be specified because either Logseq Markdown format or plain
                Markdown have the same extension `.md`.

        Notes:
            The argument `format` could be deleted with an automatic format detection.
        """
        files = []
        if os.path.isfile(path):
            files = [path]
        elif os.path.isdir(path):
            files = [str(path.resolve()) for path in pathlib.Path(path).rglob('*.md')]
        else:
            raise

        cards = []
        for f in files:
            # WARNING: add this in a configuration file
            if "Unsorted" in f:
                continue
            newCards = parser.parseFile(f, format)
            newCards = [Card(card.question, card.answer, card.tags, f) for card in newCards]
            cards += newCards

        self.format = format
        self.cardDatabase = pd.DataFrame(cards, columns=['question', 'answer', 'tags', 'path'])

    def getAnkiDatabase(self):
        """ Generate a Pandas frame compatible with Anki i.e with HTML question and answer, nested tags and a deck instead of a path.

        An Anki compatible frame has:
            - question and answer in HTML.
            - nested tags with a syntaxe `tag::nested_tag::another_nested_tag`.
            - a deck name instead of a path.
        If the original frame was generated from a Geode directory the function will deduce deck name and nested tags from the path using the Geode organisation rules.
        """
        data = self.cardDatabase.values.tolist()

        isGeodeDirectory = self.format == Format.MDGeode
        if isGeodeDirectory and ("cards" not in data[0][3].split("/")):
            isGeodeDirectory = False
        
        for card in data:
            # HTML conversion
            card[0] = markdown.markdown(card[0], extensions=['extra', 'smarty', CodeHiliteExtension(noclasses=True), 'nl2br', 'sane_lists'])
            card[1] = markdown.markdown(card[1], extensions=['extra', 'smarty', CodeHiliteExtension(noclasses=True), 'nl2br', 'sane_lists'])

            # Tags that follows the geode organisation
            if isGeodeDirectory:
                cardPath = card[3].split("/")

                deck = cardPath[cardPath.index("cards") + 2]
                # WARNING: add a config file
                if deck == 'Git' or deck == 'Linux':
                    deck = 'General'
                card[3] = deck

                cardPath = cardPath[cardPath.index("cards") + 1:]
                tags = [tag.replace(".md", "").replace(" ", "_") for tag in cardPath]
                card[2] = [tags[0]+"::"+customTag for customTag in card[2]] # Add root directory to the customs tags

                tags = ["::".join(tags)]
                card[2] = tags + card[2]
            else:
                # The deck is the filename
                # Tags are custom tags only
                filename = ntpath.basename(card[3]).split('.')[0]
                card[3] = filename

        html_database = pd.DataFrame(data, columns=['question', 'answer', 'tags', 'deck'])
        html_database['tags'] = [' '.join(map(str, l)) for l in html_database['tags']]
        return html_database

    def writeCSVAnki(self, path):
        """ Write the cards into a Anki compatible CSV file."""
        database = self.getAnkiDatabase()
        database.to_csv(path, header=False, index=False)

    def writeMarkdownGeode(self, path):
        """ Write the cards into a Geode compatible Markdown file."""
        data = self.cardDatabase.values.tolist()
        final = []

        for card in data:
            card[0] = "##### " + card[0] + " #Anki\n"
            card[1] = card[1]+"\n"
            final += card[0]
            final += card[1]

        f = open(path, 'w')
        f.write("".join(final).strip())
        f.close()

    def write(self, path, format):
        """ Write the cards into the desired format."""
        if format == Format.MDGeode:
            self.writeMarkdownGeode(path)
        elif format == Format.CSVAnki:
            self.writeCSVAnki(path)
        else:
            raise
