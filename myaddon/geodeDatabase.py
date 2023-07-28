import os
import pandas as pd
import re
import ntpath
import pathlib
from collections import namedtuple
from enum import Enum

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension

Card = namedtuple("Card", "question answer tags path")

class Format(Enum):
    MDCard = 1
    CSVCard = 2
    Logseq = 3

class fileParser:
    def __init__(self, format):
        self.format = format

    def parseFile(self, path):
        if not os.path.isfile(path):
            raise
        with open(path, 'r') as file:
            lines = file.readlines()
            if self.format == Format.MDCard:
                return self.parseMDCard(lines)
            elif self.format == Format.Logseq:
                return self.parseLogSeq(lines)
            else:
                raise

    def extractTagsFromMarkdownQuestion(self, question_with_tags):
        # It is possible to '#' in the question if this is code !!
        markerInCode = "`" in question_with_tags
        if markerInCode:
            question_no_code = question_with_tags.split("`")
            tags = question_no_code[-1].split('#')
        else:
            tags = question_with_tags.split('#')

        tags = [t for t in tags if t] #Remove empty strings
        tags = [t.strip() for t in tags]
        if not tags:
            return [], []
        question = tags[0]
        if markerInCode:
            question = "`".join(question_no_code[:-1])+"`"+question
        tags = tags[1:]
        return question, tags

    def parseMDCard(self, lines):
        lines = re.split('##### ', "".join(lines))
        lines = [w for w in lines if w] #Remove empty strings
        res = []
        for line in lines:
            question_with_tags = line.split('\n', 1)[0]
            question, tags = self.extractTagsFromMarkdownQuestion(question_with_tags)

            if "Anki" in tags:
                tags.remove("Anki") 
                answer = line.split('\n', 1)[1].strip()
                res.append(Card(question, answer, tags, ""))
        return res

    def parseLogSeq(self, lines):
        res = []
        for numLine, line in enumerate(lines):
            isAnki = "#Anki" in line
            if isAnki:
                originalDashIndex = line.index("-")

                line = line.replace("\n", "")
                line = line.replace("-", "", 1) # First occurence
                line = line.strip()
                question, tags = self.extractTagsFromMarkdownQuestion(line)
                tags.remove("Anki")

                inCode = False
                shouldContinue = True

                answer = ""
                i = 1
                # BUG: if the question as no answer
                while shouldContinue:
                    line = lines[numLine+i]

                    # Check if its a code open/close.
                    if "```" in line:
                        try:
                            codeTabulation = lines[numLine+i].index("-")+2
                            inCode = True
                        except ValueError:
                            # If there is no dash this is the end of a block code
                            inCode = False

                    # Write the answer by removing the tabulation depending of if its a code block or not.
                    if inCode: 
                        answer += lines[numLine+i][codeTabulation:]
                    else:
                        line = line.replace("-", "", 1) # First occurence
                        line = line.strip()
                        answer += line+"\n"

                    # Compare the next line tabulation with the original tabulation
                    # If its 0 level, its NOT a block part of the current question
                    # If its -1 level, its good
                    # If its -2+ level, its a list
                    # If no dash and not inCode: BUG
                    # If no dash and inCode: GOOD
                    i += 1
                    if numLine+i >= len(lines):
                        break
                    nextLine = lines[numLine+i]
                    try:
                        dashIndex = nextLine.index("-")
                        if dashIndex - originalDashIndex == 0:
                            shouldContinue = False
                    except ValueError:
                        # If there is no dash
                        if not inCode:
                            raise


                res.append(Card(question, answer, tags, ""))
                # Code to write in Markdown format
                # answer = answer.strip().split("\n")
                # answer = "\n".join(answer)
                # data.append(question+"\n"+answer+"\n\n")
        return res

class Database:
    def __init__(self, path="/home/thomas/note/geode/cards", format=Format.MDCard):
        data = self.parse(path, format)
        self.cardDatabase = pd.DataFrame(data, columns=['question', 'answer', 'tags', 'path'])

    def parse(self, path, format):
        parser = fileParser(format)

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
            newCards = parser.parseFile(f)
            newCards = [Card(card.question, card.answer, card.tags, f) for card in newCards]
            cards += newCards

        return cards

    def getAnkiDatabase(self, automaticGeodeTags=True):
        data = self.cardDatabase.values.tolist()

        if automaticGeodeTags and ("cards" not in data[0][3].split("/")):
            automaticGeodeTags = False
        
        for card in data:
            # HTML conversion
            card[0] = markdown.markdown(card[0], extensions=['extra', 'smarty', CodeHiliteExtension(noclasses=True), 'nl2br', 'sane_lists'])
            card[1] = markdown.markdown(card[1], extensions=['extra', 'smarty', CodeHiliteExtension(noclasses=True), 'nl2br', 'sane_lists'])

            # Tags that follows the geode organisation
            if automaticGeodeTags:
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

    def writeAnkiCSV(self, path, automaticGeodeTags=True):
        database = self.getAnkiDatabase(automaticGeodeTags)
        database.to_csv(path, header=False, index=False)

    def writeMarkdown(self, path):
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
