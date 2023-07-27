#Conversion

from os import listdir
from os.path import join, isfile, dirname, abspath
import sys
import pathlib
import warnings

sys.path.append(
    str(pathlib.Path(__file__).parent.resolve().parent.resolve().joinpath("venv/lib/python3.9/site-packages")))

import pandas as pd

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension

from bs4 import BeautifulSoup

def extract_tags(line):
    words = line.split(" ")
    tags = [word.replace('#', '') for word in words if word and word[0] == '#']
    final_line = []
    for word in words:
        if word and word[0] != "#":
            final_line.append(word)
    return " ".join(final_line), tags


def extractDataFromPath(path):
    try:
        fpath = path.split("/")

        filename = fpath[fpath.index("cards") + 2]

        noteIndex = fpath.index("cards")
        fpath = fpath[noteIndex + 1:]
        tags = [tag.replace(".md", "").replace(" ", "_") for tag in fpath]
        root_tag = tags[0]
        tags = ["::".join(tags)]

        return filename, tags, root_tag

    except IndexError:
        if not path[-1] == "README.md":
            print("Error with file: " + path)
            raise IndexError


def convertFilename(data, filenames, to):
    for name in filenames:
        data.loc[data['filename'] == name, 'filename'] = to


# notedir = "notes"
# ankidir = "anki"
#
# searchPath=dirname(abspath(__file__))+"/"+notedir
# writePath=dirname(abspath(__file__))+"/"+ankidir

#finalCSVFiles = []
#for name in filenames:
#    subset = frame[frame['filename'] == name][['question', 'answer', 'tags']]
#    finalCSVFiles.append(writePath + "/" + name + "_test.csv")
#    subset.to_csv(finalCSVFiles[:-1], header=False, index=False)

# Import

from aqt.utils import showInfo, qconnect
from aqt.qt import *
from anki.collection import ImportCsvRequest
from aqt import mw

def generateDatabase() -> pd.DataFrame:
    searchPath = "/home/thomas/note/geode/cards"

    mdfiles = [str(path.resolve()) for path in pathlib.Path(searchPath).rglob('*.md')]

    data = []
    for f in mdfiles:
        markdownFile = "".join(open(f, 'r').readlines())
        html = markdown.markdown(markdownFile, extensions=['extra', 'smarty', CodeHiliteExtension(noclasses=True), 'nl2br', 'sane_lists'])

        filename, tags, root_tag = extractDataFromPath(f)
        if filename == "Unsorted":
            continue

        parser = BeautifulSoup(html, 'html.parser')
        for question in parser.find_all('h5'):
            if '#Anki' not in question.text:
                continue
            html_answer = ""
            nextSib = question.next_sibling
            while nextSib is not None and nextSib.name != 'h5':
                text = str(nextSib)
                if nextSib.name == 'p':
                    text = text.replace("![[", '<br><img src="')
                    text = text.replace("]]", '"><br>')
                html_answer += text
                nextSib = nextSib.next_sibling
            html_question = str(question).replace("<h5>", "").replace("</h5>", "")
            html_question_without_tags, custom_tags = extract_tags(html_question)
            custom_tags = custom_tags[1:]
            custom_tags = [root_tag+"::"+tag for tag in custom_tags]
            data.append((html_question_without_tags, html_answer, tags+custom_tags, filename))

    frame = pd.DataFrame(data, columns=['question', 'answer', 'tags', 'filename'])
    frame['tags'] = [' '.join(map(str, l)) for l in frame['tags']]

    convertFilename(frame, ['Git', 'Linux', 'General'], 'General')

    return frame

def importCSV(frame) -> None:

    writePath = "/home/thomas/note/geode/anki/ankiDatabase.csv"
    frame.to_csv(writePath, header=False, index=False)

    col = mw.col
    #path = "/home/thomas/note/geode/anki/Python_test.csv"
    path = writePath
    metadata = col.get_csv_metadata(path=path, delimiter=4)
    metadata.tags_column = 3
    metadata.deck_column = 4

    response = col.import_csv(ImportCsvRequest(path=path, metadata=metadata))
    #print(response.log.found_notes, list(response.log.updated), list(response.log.new))
    showInfo("[{}] cards added and [{}] cards updated\n".format(len(list(response.log.new)), len(list(response.log.updated))))

def syncDatabase(mdFrame) -> None:

    col = mw.col

    data = []
    ids = mw.col.find_cards("")
    for id in ids:
        card = mw.col.get_card(id)
        question = card.question()
        answer = card.answer()
        tag = card.note().tags
        deck = [iDeck.name for iDeck in col.decks.all_names_and_ids() if iDeck.id == card.current_deck_id()][0]
        cardid = card.id

        # Allow to get the user flag
        #flag = card.user_flag()

        # WARNING: BUG PRONE PARSE !! DO IT BETTER BY CONVERTING TO HTML AND REMOVE THE STYLE
        question = question.split('style>')[-1].replace("\n", "")
        data.append((question, answer, tag, deck, cardid))

    ankiFrame = pd.DataFrame(data, columns=['question', 'answer', 'tags', 'filename', 'id'])

    ankiFrame['from'] = 'Anki'
    mdFrame['from'] = 'Markdown'
    difference = pd.concat([mdFrame, ankiFrame]).drop_duplicates(subset='question', keep=False)

    ankiToFlag = difference[difference['from'] == 'Anki']
    ankiToFlag.reset_index()

    flag = "NOT_IN_GEODE"
    ids = col.find_notes("tag:"+flag)
    for id in ids:
        note = col.get_note(id)
        note.remove_tag(flag)
        col.update_note(note)

    newlyFlagged = 0
    for index, row in ankiToFlag.iterrows():
        card = col.get_card(int(row['id']))
        note = col.get_note(card.note().id)
        newlyFlagged += 1
        note.add_tag(flag)
        col.update_note(note)

    showInfo("Database synced\n [{}] total cards in Anki but not in Geode.\n".format(newlyFlagged))

def syncDatabaseAction() -> None:
    frame = generateDatabase()
    syncDatabase(frame)

def importCSVAction() -> None:
    frame = generateDatabase()
    importCSV(frame)
    syncDatabase(frame)

actionSyncDatabase = QAction("Sync database", mw)
qconnect(actionSyncDatabase.triggered, syncDatabaseAction)
mw.form.menuTools.addAction(actionSyncDatabase)

actionImportCSV = QAction("Import CSV", mw)
qconnect(actionImportCSV.triggered, importCSVAction)
mw.form.menuTools.addAction(actionImportCSV)
