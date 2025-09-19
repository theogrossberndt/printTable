import curses
from .chars import Chars, SepClass
from typing import List, Union
from .connectable import Connectable
from .cell import Cell, _CellChars

class Line(Connectable):
	NORMAL: int = 0
	FOCUSED: int = 1
	HEADER: int = 2
	GROUP: int = 3
	OTHER: int = 4

	colorsInitialized: bool = False

	@staticmethod
	def getElementDecorator(lineType: int) -> int:
		if not Line.colorsInitialized:
			curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
			curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
			curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
			Line.colorsInitialized = True

		if lineType == Line.HEADER:
			return curses.color_pair(1) | curses.A_BOLD

		if lineType == Line.GROUP:
			return curses.color_pair(2) | curses.A_BOLD

		if lineType == Line.FOCUSED:
			return curses.color_pair(2) | curses.A_REVERSE | curses.A_BOLD

		if lineType == Line.OTHER:
			return curses.color_pair(3)

		return curses.color_pair(2)


	def __init__(self, colWidths: List[int], content: List[str], parent, sepClass: SepClass = None, elDecorators: Union[int, List[int]] = None):
		self.colWidths = colWidths
		self.content = []
		self.parents = [parent]
		self.elDecorators = []
		self.sepClass = sepClass if sepClass is not None else Chars.contentSep
		self.y = 0

		iContent = content[::-1]
		if elDecorators is None or isinstance(elDecorators, int):
			iElDecorators = [elDecorators if elDecorators is not None else Line.NORMAL for _ in range(len(content))]
		else:
			iElDecorators = elDecorators[::-1]

		for c in range(len(content)):
			self.insertContentCell(iContent[c], iElDecorators[c])


	def insertContentCell(self, content: str, elDecorator: int, parent = None):
		if len(self.content) == len(self.colWidths):
			return

		self.content.insert(0, content)
		self.elDecorators.insert(0, elDecorator)
		if parent is not None:
			self.parents.append(parent)


	def draw(self, window: curses.window, y: int, sepClass: SepClass = None):
		self.y = y

		# Useful for hline calculations
		effSepClass = sepClass if sepClass is not None else self.sepClass

		fwDecorator = 0

		startX: int = 0
		maxY, maxX = window.getmaxyx()
		# If this is out of window range exit gracefully
		if y >= maxY or y < 0:
			return startX

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
				effElDecorator = Line.getElementDecorator(self.elDecorators[c - firstContentC])

			cell = Cell(content, self.colWidths[c])
			startX = cell.draw(window, y, startX, effElDecorator, fwDecorator, cellChars, maxX)

			if startX >= maxX:
				break

		# The line is responsible for drawing the last wall at the full width and space chars before it
		if len(effSepClass.space.strip()) > 0 and startX < maxX:
			window.addstr(y, startX, (maxX - len(effSepClass.endWall) - startX) * effSepClass.space, fwDecorator)
		window.addstr(y, maxX-len(effSepClass.endWall)-1, effSepClass.endWall, fwDecorator)

		return startX

	def getTopColWidths(self):
		return self.colWidths
	def getBottomColWidths(self):
		return self.colWidths

	def getTopContentLen(self):
		return len(self.content)
	def getBottomContentLen(self):
		return len(self.content)
