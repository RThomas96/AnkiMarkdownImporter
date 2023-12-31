"""Extract cards from a file according to its format.

Handled formats:
    - Markdown
    - Logseq markdown

Typical usage example:
  data = parseFile("path/to/my/file.md", Format.MDGeode)
"""
import os
import re
from enum import Enum

from card import Card

class Format(Enum):
    MDGeode = 1
    CSVAnki = 2
    MDLogseq = 3

def _extractTagsFromMarkdownQuestion(question_with_tags):
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

def parseMDGeode(lines):
    lines = re.split('##### ', "".join(lines))
    lines = [w for w in lines if w] #Remove empty strings
    res = []
    for line in lines:
        question_with_tags = line.split('\n', 1)[0]
        question, tags = _extractTagsFromMarkdownQuestion(question_with_tags)

        if "Anki" in tags:
            tags.remove("Anki") 
            answer = line.split('\n', 1)[1].strip()
            res.append(Card(question, answer, tags, ""))
    return res

def parseLogSeq(lines):
    res = []
    for numLine, line in enumerate(lines):
        isAnki = "#Anki" in line
        if isAnki:
            originalDashIndex = line.index("-")

            line = line.replace("\n", "")
            line = line.replace("-", "", 1) # First occurence
            line = line.strip()
            question, tags = _extractTagsFromMarkdownQuestion(line)
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
                    try:
                        dashIndex = line.index("-")
                    except ValueError:
                        if '```' in line:
                            dashIndex = originalDashIndex
                        else:
                            raise
                    line = line.replace("-", "", 1) # First occurence
                    line = line.strip()
                    if dashIndex - originalDashIndex > 1: # If we are at indentation level -2, this is a list
                        line = "- "+line
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

def parseFile(path, format):
    if not os.path.isfile(path):
        raise
    with open(path, 'r') as file:
        lines = file.readlines()
        if format == Format.MDGeode:
            return parseMDGeode(lines)
        elif format == Format.MDLogseq:
            return parseLogSeq(lines)
        else:
            raise

