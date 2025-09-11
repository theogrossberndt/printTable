import curses
from .chars import Chars, SepClass
from typing import List

class _CellChars:
	def __init__(self, start, space, padding):
		self.start = start
		self.space = space
		self.padding = padding

class Line:
	NORMAL: int = 0
	HEADER: int = 1
	GROUP: int = 2

	colorsInitialized: bool = False

	@staticmethod
	def getElementDecorator(lineType: int, focused: bool) -> int:
		if not Line.colorsInitialized:
			curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
			curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
			curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
			Line.colorsInitialized = True


		focuser = (curses.A_REVERSE | curses.A_ITALIC) if focused else 0

		if lineType == Line.HEADER:
			return curses.color_pair(1) | curses.A_BOLD | focuser

		if lineType == Line.GROUP:
			return curses.color_pair(2) | curses.A_BOLD | focuser

		return focuser


	def __init__(self, content: List[str], node, lineType: int = None, sepClass: SepClass = None, colWidths: List[int] = None):
		self.content: List[str] = content
		self.node = node
		self.colWidths = self.node.colWidths if colWidths is None else colWidths
		self.lineType: int = lineType if lineType is not None else Line.NORMAL
		self.sepClass = sepClass if sepClass is not None else Chars.contentSep

		if len(self.content) > len(self.colWidths):
			self.content = self.content[-1 * len(self.colWidths):]

		# For convenience of building the cells list, flip colWidths and content and build cells backwards
		iContent = self.content[::-1]
		iColWidths = self.colWidths[::-1]

		# Build content cells
		self.contentCells: List[Cell] = [Cell(iContent[c], iColWidths[c]) for c in range(len(self.content))]
		self.contentCells = self.contentCells[::-1]

		# Build enough empty cells to fill out the rest of the column
		self.emptyCells: List[Cell] = [Cell('', iColWidths[c]) for c in range(len(self.contentCells), len(self.colWidths))]
		self.emptyCells = self.emptyCells[::-1]

		# In the case of header lines, no cells are focusable
		# In normal lines, all content cells are focusable
		self.focusable = [] if self.lineType == Line.HEADER else self.contentCells
		self.isFocusable = len(self.focusable) > 0


	def draw(self, window: curses.window, y: int, isFocused: bool = None, sepClass: SepClass = None, x: int = None, fullWidth: bool = True):
		focused = isFocused if isFocused is not None else self.node.isFocused and self.isFocusable

		# Useful for hline calculations
		effSepClass = sepClass if sepClass is not None else self.sepClass

		elDecorator = Line.getElementDecorator(self.lineType, False)
		fwDecorator = 0

		startX: int = x if x is not None else 0
		maxY, maxX = window.getmaxyx()

		for cell in self.emptyCells:
			cellChars = _CellChars(effSepClass.eCenter, effSepClass.eSpace, effSepClass.padding)
			startX = cell.draw(window, y, startX, elDecorator, fwDecorator, cellChars, maxX)
			if startX >= maxX:
				break

		isFirst = True
		for c in range(len(self.contentCells)):
			start = effSepClass.startWall if isFirst else effSepClass.centerWall
			effElDecorator = Line.getElementDecorator(self.lineType, focused and c == self.node.focusedIdx)

			cellChars = _CellChars(start, effSepClass.space, effSepClass.padding)
			startX = self.contentCells[c].draw(window, y, startX, effElDecorator, fwDecorator, cellChars, maxX)
			isFirst = False
			if startX >= maxX:
				break

		# The line is responsible for drawing the last wall at the full width and space chars before it
		if fullWidth:
			if len(effSepClass.space.strip()) > 0 and startX < maxX:
				window.addstr(y, startX, (maxX - len(effSepClass.endWall) - startX) * effSepClass.space, fwDecorator)
			window.addstr(y, maxX-len(effSepClass.endWall), effSepClass.endWall, fwDecorator)
		return startX


class Cell:
	def __init__(self, content: str, colWidth: int):
		self.content = str(content)
		self.colWidth = colWidth


	def _drawStr(self, window: curses.window, y: int, startX: int, val: str, decorator: int, maxX: int, isContent: bool = False):
		if len(val.strip()) == 0:
			return startX + len(val)

		if startX + len(val) < maxX:
			window.addstr(y, startX, val, decorator)
		else:
			repVal = val[:maxX - startX]
			if isContent:
				repVal = repVal[:-3] + '...'
			window.addstr(y, startX, repVal, decorator)
		return startX + len(val)


	def draw(self, window: curses.window, y: int, startX: int, elDecorator: int, fwDecorator: int, cellChars: _CellChars, maxX: int):
		# Draw the left separator
		startX = self._drawStr(window, y, startX, cellChars.start, fwDecorator, maxX)

		# Draw left padding
		startX = self._drawStr(window, y, startX, cellChars.space * cellChars.padding, fwDecorator, maxX)

		# Draw the content
		startX = self._drawStr(window, y, startX, self.content, elDecorator | fwDecorator, maxX, True)

		# Draw the remaining space from the col
		startX = self._drawStr(window, y, startX, cellChars.space * (self.colWidth - len(self.content)), elDecorator | fwDecorator, maxX)

		# Draw the right padding
		startX = self._drawStr(window, y, startX, cellChars.space * cellChars.padding, fwDecorator, maxX)

		return startX
