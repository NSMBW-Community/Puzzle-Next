'''
Licensed under the terms of the MIT License
https://github.com/luchko/QCodeEditor
https://github.com/N-I-N-0/Puzzle-Next
@author: Ivan Luchko (luchko.ivan@gmail.com)
@author: Nin0#2257

This module contains the light QPlainTextEdit based QCodeEditor widget which 
provides the line numbers bar and the syntax and the current line highlighting.
'''
try:
    import PyQt5 as PyQt
    pyQtVersion = "PyQt5"
except ImportError:
    try:
        import PySide2 as PyQt
        pyQtVersion = "PySide2"
    except ImportError:
        raise ImportError("neither PyQt5 or PySide2 found")

# imports requied PyQt modules
if pyQtVersion == "PyQt5":
    from PyQt5.QtCore import Qt, QRect, QRegExp
    from PyQt5.QtWidgets import QWidget, QTextEdit, QPlainTextEdit
    from PyQt5.QtGui import (QColor, QPainter, QFont, QSyntaxHighlighter,
                             QTextFormat, QTextCharFormat)
else:
    from PySide2.QtCore import Qt, QRect, QRegExp
    from PySide2.QtWidgets import QWidget, QTextEdit, QPlainTextEdit
    from PySide2.QtGui import (QColor, QPainter, QFont, QSyntaxHighlighter,
                               QTextFormat, QTextCharFormat)
# classes definition

class XMLHighlighter(QSyntaxHighlighter):
    '''
    Class for highlighting xml text inherited from QSyntaxHighlighter

    reference:
        http://www.yasinuludag.com/blog/?p=49
    '''
    def __init__(self, parent=None):
        super(XMLHighlighter, self).__init__(parent)

        self.highlightingRules = []
        self.searchRules = []

        self.xmlElementFormat = QTextCharFormat()
        self.xmlElementFormat.setForeground(QColor("#00ee00"))
        self.highlightingRules.append((QRegExp("\\b[A-Za-z0-9_]+(?=[\s/>])"), self.xmlElementFormat))

        self.xmlAttributeFormat = QTextCharFormat()
        self.xmlAttributeFormat.setFontItalic(True)
        self.xmlAttributeFormat.setForeground(QColor("#d000d0"))
        self.highlightingRules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\=)"), self.xmlAttributeFormat))
        self.highlightingRules.append((QRegExp("="), self.xmlAttributeFormat))

        self.valueFormat = QTextCharFormat()
        self.valueFormat.setForeground(QColor("#55dddd"))
        self.valueStartExpression = QRegExp("\"")
        self.valueEndExpression = QRegExp("\"(?=[\s></])")

        self.singleLineCommentFormat = QTextCharFormat()
        self.singleLineCommentFormat.setForeground(QColor("#b3b3b3"))
        self.highlightingRules.append((QRegExp("<!--[^\n]*-->"), self.singleLineCommentFormat))

        self.textFormat = QTextCharFormat()
        self.textFormat.setForeground(QColor("#FFFFFF"))
        # (?<=...)  - lookbehind is not supported
        self.highlightingRules.append((QRegExp(">(.+)(?=</)"), self.textFormat))

        self.keywordFormat = QTextCharFormat()
        self.keywordFormat.setForeground(QColor("#FFFFFF"))
        keywordPatterns = ["\\b?xml\\b", "/>", ">", "<", "</"] 
        self.highlightingRules += [(QRegExp(pattern), self.keywordFormat) for pattern in keywordPatterns]

    def setHighlighterColors(self, isDarkMode):
        if isDarkMode:
            self.xmlElementFormat.setForeground(QColor("#00ee00"))
            self.xmlAttributeFormat.setForeground(QColor("#d000d0"))
            self.valueFormat.setForeground(QColor("#55dddd"))
            self.singleLineCommentFormat.setForeground(QColor("#b3b3b3"))
            self.textFormat.setForeground(QColor("#FFFFFF"))
            self.keywordFormat.setForeground(QColor("#FFFFFF"))
        else:
            self.xmlElementFormat.setForeground(QColor("#22863a"))
            self.xmlAttributeFormat.setForeground(QColor("#6f42c1"))
            self.valueFormat.setForeground(QColor("#032f62"))
            self.singleLineCommentFormat.setForeground(QColor("#6a737d"))
            self.textFormat.setForeground(QColor("#24292e"))
            self.keywordFormat.setForeground(QColor("#24292e"))        

    #VIRTUAL FUNCTION WE OVERRIDE THAT DOES ALL THE COLLORING
    def highlightBlock(self, text):
        #for every pattern
        for pattern, format in self.highlightingRules: 
            #Create a regular expression from the retrieved pattern
            expression = QRegExp(pattern) 
            #Check what index that expression occurs at with the ENTIRE text
            index = expression.indexIn(text) 
            #While the index is greater than 0
            while index >= 0:
                #Get the length of how long the expression is true, set the format from the start to the length with the text format
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                #Set index to where the expression ends in the text
                index = expression.indexIn(text, index + length)


        #HANDLE QUOTATION MARKS NOW.. WE WANT TO START WITH " AND END WITH ".. A THIRD " SHOULD NOT CAUSE THE WORDS INBETWEEN SECOND AND THIRD TO BE COLORED
        self.setCurrentBlockState(0)
        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.valueStartExpression.indexIn(text)
        while startIndex >= 0:
            endIndex = self.valueEndExpression.indexIn(text, startIndex)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.valueEndExpression.matchedLength()
            self.setFormat(startIndex, commentLength, self.valueFormat)
            startIndex = self.valueStartExpression.indexIn(text, startIndex + commentLength);

        for word in self.searchRules:
            expression = QRegExp(word)
            expression.setCaseSensitivity(Qt.CaseInsensitive)
            index = expression.indexIn(text)
            while index >= 0: 
                length = expression.matchedLength()
                keywordFormat = QTextCharFormat()
                keywordFormat.setBackground(QColor("#FF0000"))
                self.setFormat(index, length, keywordFormat)
                index = expression.indexIn(text, index + length)


class SearchHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(SearchHighlighter, self).__init__(parent)

        self.searchRules = []

    def highlightBlock(self, text):
        for word in self.searchRules:
            expression = QRegExp(word)
            expression.setCaseSensitivity(Qt.CaseInsensitive)
            index = expression.indexIn(text)
            while index >= 0: 
                length = expression.matchedLength()
                keywordFormat = QTextCharFormat()
                keywordFormat.setBackground(QColor("#FF0000"))
                self.setFormat(index, length, keywordFormat)
                index = expression.indexIn(text, index + length)


class QCodeEditor(QPlainTextEdit):
    '''
    QCodeEditor inherited from QPlainTextEdit providing:
        numberBar - set by DISPLAY_LINE_NUMBERS flag equals True
        curent line highligthing - set by HIGHLIGHT_CURRENT_LINE flag equals True
        setting up QSyntaxHighlighter

    references:
        https://john.nachtimwald.com/2009/08/19/better-qplaintextedit-with-line-numbers/    
        http://doc.qt.io/qt-5/qtwidgets-widgets-codeeditor-example.html
    '''

    class NumberBar(QWidget):
        '''class that deifnes textEditor numberBar'''
        def __init__(self, editor):
            QWidget.__init__(self, editor)
            
            self.editor = editor
            self.editor.blockCountChanged.connect(self.updateWidth)
            self.editor.updateRequest.connect(self.updateContents)
            self.font = QFont()
            self.numberBarColor = QColor("#171717")
            self.numberBarFontColor = QColor("#717171")
            self.numberBarSelectedFontColor = QColor("#FFFFFF")


        def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(event.rect(), self.numberBarColor)

            block = self.editor.firstVisibleBlock()

            # Iterate over all visible text blocks in the document.
            while block.isValid():
                blockNumber = block.blockNumber()
                block_top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()

                # Check if the position of the block is out side of the visible area.
                if not block.isVisible() or block_top >= event.rect().bottom():
                    break

                # We want the line number for the selected line to be bold.
                if blockNumber == self.editor.textCursor().blockNumber() and self.editor.hasFocus():
                    self.font.setBold(True)
                    painter.setPen(self.numberBarSelectedFontColor)
                else:
                    self.font.setBold(False)
                    painter.setPen(self.numberBarFontColor)
                painter.setFont(self.font)

                # Draw the line number right justified at the position of the line.
                paint_rect = QRect(0, int(block_top), self.width(), self.editor.fontMetrics().height())
                painter.drawText(paint_rect, Qt.AlignRight, str(blockNumber+1))

                block = block.next()

            painter.end()

            QWidget.paintEvent(self, event)


        def getWidth(self):
            count = self.editor.blockCount()
            width = self.fontMetrics().width(str(count)) + 10
            return width


        def updateWidth(self):
            width = self.getWidth()
            if self.width() != width:
                self.setFixedWidth(width)
                self.editor.setViewportMargins(width, 0, 0, 0);


        def updateContents(self, rect, scroll):
            if scroll:
                self.scroll(0, scroll)
            else:
                self.update(0, rect.y(), self.width(), rect.height())

            if rect.contains(self.editor.viewport().rect()):   
                fontSize = self.editor.currentCharFormat().font().pointSize()
                self.font.setPointSize(fontSize)
                self.font.setStyle(QFont.StyleNormal)
                self.updateWidth()


    def __init__(self, DISPLAY_LINE_NUMBERS=True, HIGHLIGHT_CURRENT_LINE=True, SyntaxHighlighter=None, *args):
        '''
        Parameters
        ----------
        DISPLAY_LINE_NUMBERS : bool 
            switch on/off the presence of the lines number bar
        HIGHLIGHT_CURRENT_LINE : bool
            switch on/off the current line highliting
        SyntaxHighlighter : QSyntaxHighlighter
            should be inherited from QSyntaxHighlighter
        '''
        super(QCodeEditor, self).__init__()

        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.DISPLAY_LINE_NUMBERS = DISPLAY_LINE_NUMBERS

        if DISPLAY_LINE_NUMBERS:
            self.number_bar = self.NumberBar(self)

        if HIGHLIGHT_CURRENT_LINE:
            self.currentLineNumber = None
            self.currentLineColor = QColor("#171717")
            self.cursorPositionChanged.connect(self.highligtCurrentLine)
            self.original_out = self.focusOutEvent
            self.focusOutEvent = self.focusOut

        if SyntaxHighlighter is not None: # add highlighter to textdocument
           self.highlighter = SyntaxHighlighter(self.document())


        self.appendPlainText("\n\n\n\n\n\n\n\n\n\n")
        self.clear()

    def changeStyle(self, isDarkMode):
        if isDarkMode:
            self.number_bar.numberBarColor = QColor("#171717")
            self.number_bar.numberBarFontColor = QColor("#717171")
            self.number_bar.numberBarSelectedFontColor = QColor("#FFFFFF")
            self.currentLineColor = QColor("#171717")
        else:
            self.number_bar.numberBarColor = QColor("#C1C1C1")
            self.number_bar.numberBarFontColor = QColor("#171717")
            self.number_bar.numberBarSelectedFontColor = QColor("#000000")
            self.currentLineColor = QColor("#C1C1C1")
        self.highligtCurrentLine(True)

    def focusOut(self, event):
        self.original_out(event)
        self.highligtCurrentLine(True)


    def resizeEvent(self, *e):
        '''overload resizeEvent handler'''
        if self.DISPLAY_LINE_NUMBERS:   # resize number_bar widget
            cr = self.contentsRect()
            rec = QRect(cr.left(), cr.top(), self.number_bar.getWidth(), cr.height())
            self.number_bar.setGeometry(rec)
        QPlainTextEdit.resizeEvent(self, *e)


    def highligtCurrentLine(self, hidden = False):
        if(hidden):
            hi_selection = QTextEdit.ExtraSelection()
            hi_selection.cursor = self.textCursor()
            hi_selection.cursor.clearSelection()
            self.setExtraSelections([hi_selection])
        else:
            newCurrentLineNumber = self.textCursor().blockNumber()
            if newCurrentLineNumber != self.currentLineNumber:
                self.currentLineNumber = newCurrentLineNumber
                hi_selection = QTextEdit.ExtraSelection()
                hi_selection.format.setBackground(self.currentLineColor)
                hi_selection.format.setProperty(QTextFormat.FullWidthSelection, True)
                hi_selection.cursor = self.textCursor()
                hi_selection.cursor.clearSelection()
                self.setExtraSelections([hi_selection])
