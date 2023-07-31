"""Import cards from a Geode database."""

import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.resolve().parent.resolve().joinpath("venv/lib/python3.9/site-packages")))
sys.path.append(str(pathlib.Path(__file__).parent.resolve()))

import pandas as pd
from geodeDatabase import Database

from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import *
from anki.collection import ImportCsvRequest

def importCSV(database) -> None:
    writePath = "/home/thomas/note/geode/anki/ankiDatabase.csv"
    database.write(writePath, Format.CSVAnki)

    col = mw.col
    #path = "/home/thomas/PycharmProjects/ankiMarkdownImporter/myaddon/test/AnkiCSVTestGeode.csv"
    path = writePath
    metadata = col.get_csv_metadata(path=path, delimiter=4)
    metadata.tags_column = 3
    metadata.deck_column = 4

    response = col.import_csv(ImportCsvRequest(path=path, metadata=metadata))
    #print(response.log.found_notes, list(response.log.updated), list(response.log.new))
    showInfo("[{}] cards added and [{}] cards updated\n".format(len(list(response.log.new)), len(list(response.log.updated))))

def syncDatabase(database) -> None:
    """Add a tag 'NOT_IN_GEODE' for all cards not found in the Geode database."""
    mdFrame = database.getAnkiDatabase()
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
    database = Database()
    syncDatabase(database)

def importCSVAction() -> None:
    database = Database()
    importCSV(database)
    syncDatabase(database)

actionSyncDatabase = QAction("Sync database", mw)
qconnect(actionSyncDatabase.triggered, syncDatabaseAction)
mw.form.menuTools.addAction(actionSyncDatabase)

actionImportCSV = QAction("Import CSV", mw)
qconnect(actionImportCSV.triggered, importCSVAction)
mw.form.menuTools.addAction(actionImportCSV)
