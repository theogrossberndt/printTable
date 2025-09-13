import curses
from .chars import Chars, SepClass
from typing import List, Union

class _CellChars:
	def __init__(self, start, space, padding):
		self.start = start
		self.space = space
		self.padding = padding

class LineBuilder:
	NORMAL: int = 0
	FOCUSED: int = 1
	HEADER: int = 1
	GROUP: int = 2

	colorsInitialized: bool = False

	@staticmethod
	def getElementDecorator(lineType: int) -> int:
		if not LineBuilder.colorsInitialized:
			curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
			curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
			curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
			LineBuilder.colorsInitialized = True

		if lineType == LineBuilder.HEADER:
			return curses.color_pair(1) | curses.A_BOLD

		if lineType == LineBuilder.GROUP:
			return curses.color_pair(2) | curses.A_BOLD

		if lineType == LineBuilder.FOCUSED:
			return curses.color_pair(2) | curses.A_REVERSE | curses.A_ITALIC

		return curses.color_pair(2)


	def __init__(self, colWidths: List[int], content: List[str] = [], sepClass: SepClass = None, elDecorators: Union[int, List[int]] = None):
		self.colWidths = colWidths
		self.content = []
		self.elDecorators = []
		self.sepClass = sepClass if sepClass is not None else Chars.contentSep

		iContent = content[::-1]
		if elDecorators is None or isinstance(elDecorators, int):
			iElDecorators = [elDecorators if elDecorators is not None else LineBuilder.NORMAL for _ in range(len(content))]
		else:
			iElDecorators = elDecorators[::-1]

		for c in range(len(content)):
			self.insertContentCell(iContent[c], iElDecorators[c])


	def insertContentCell(self, content: str, elDecorator: int):
		if len(self.content) == len(self.colWidths):
			return

		self.content.insert(0, content)
		self.elDecorators.insert(0, elDecorator)


	def draw(self, window: curses.window, y: int, sepClass: SepClass = None, fullWidth: bool = True):
		# Useful for hline calculations
		effSepClass = sepClass if sepClass is not None else self.sepClass

		fwDecorator = 0

		startX: int = 0
		maxY, maxX = window.getmaxyx()

		# The number of empty cells is the difference between the colWidths and the content
		firstContentC = len(self.colWidths) - len(self.content)
		for c in range(len(self.colWidths)):
			if c < firstContentC:
				cellChars = _CellChars(effSepClass.eCenter, effSepClass.eSpace, effSepClass.padding)
				content = ''
				effElDecorator = 0
			else:
				cellChars = _CellChars(effSepClass.startWall if c == firstContentC else effSepClass.centerWall, effSepClass.space, effSepClass.padding)
				content = self.content[c - firstContentC]
				effElDecorator = LineBuilder.getElementDecorator(self.elDecorators[c - firstContentC])

			cell = Cell(content, self.colWidths[c])
			startX = cell.draw(window, y, startX, effElDecorator, fwDecorator, cellChars, maxX)

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
