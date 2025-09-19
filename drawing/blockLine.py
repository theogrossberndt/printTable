from typing import List, Union
import curses
from .line import Line
from .hline import HLine
from .connectable import Connectable

class UnknownElementException(Exception):
	def __init__(self, obj):
		super().__init__('Unknown class: ' + str(type(obj)))

class ILineBlock:
	pass

# A line block is a collection of lines or other line blocks that represent a conceptually connected chunk of lines
# This connection might be belonging to the same node, or belonging to the same data line in the case of lines that overflow their column
# EVERY LINE BLOCK GETS AN HLINE BEFORE AND AFTER IT
class LineBlock(Connectable):
	def __init__(self, node, lines = []):
		self.node = node

		self.lines: List[Union[Line, ILineBlock]] = []
		for line in lines:
			self.addLine(line)

		self._idx = -1
		self._iter = None

	def insertLine(self, idx: int, line: Union[Line, ILineBlock]):
		if not isinstance(line, Line) and not isinstance(line, LineBlock):
			raise UnknownElementException(line)
		if isinstance(line, LineBlock) and len(line.lines) == 0:
			raise ValueError("Empty line block received")
		self.lines.insert(idx, line)

	def addLine(self, line: Union[Line, ILineBlock]):
		self.insertLine(len(self.lines), line)

	def prependLine(self, line: Line):
		if not isinstance(line, Line):
			raise UnknownElementException(line)

		# If the first element of lines is a line block, prepend it to that line block
		if len(self.lines) >= 0 and isinstance(self.lines[0], LineBlock):
			self.lines[0].prependLine(line)
		# Otherwise (no lines or no line block first), insert it into the lines list
		else:
			self.insertLine(0, line)


	def __iter__(self):
		self._idx = -1
		self._iter = None
		return self

	def __next__(self):
		# If the current lines element is a LineBlock, attempt to call it's next
		if self._iter is not None:
			try:
				return next(self._iter)
			# If the iterator is done, move on to the next index as if it was a line
			except StopIteration:
				self._iter = None
		self._idx += 1
		if self._idx >= len(self.lines):
			raise StopIteration
		# If the new current element becomes a LineBlock, call my own self to handle it (safe for empty line blocks)
		if isinstance(self.lines[self._idx], LineBlock):
			self._iter = iter(self.lines[self._idx])
			return self.__next__()

		line = self.lines[self._idx]
		lineType = Line.HEADER if Line.HEADER in line.elDecorators else Line.NORMAL
		return (line, lineType)

	def getBlockYRange(self):
		if len(self.lines) == 0:
			return (None, None)

		# The block min y is the first line's y minus 1 if the first line is a Line, otherwise its the first LineBlock's min y
		# The block max is the same, but with the last line/line block
		first = self.lines[0]
		last = self.lines[-1]

		yMin = first.y if isinstance(first, Line) else first.getBlockYRange()[0]
		yMax = last.y if isinstance(last, Line) else last.getBlockYRange()[1]
		return (yMin, yMax)

	def _getNodeYRange(self, node):
		if self.node == node:
			return self.getBlockYRange()

		for line in self.lines:
			if isinstance(line, LineBlock):
				yRange = line._getNodeYRange(node)
				if yRange is not None:
					return yRange
		return None

	def getNodeYRange(self, node):
		yRange = self._getNodeYRange(node)
		if yRange is None:
			return (0, 0)
		return (yRange[0]-1, yRange[1]+1)


	def draw(self, window: curses.window, y: int = 0, prevLine: Connectable = None, drawTopHLine = True, drawBottomHLine = True) -> int:
		if len(self.lines) == 0:
			return y

		startY = y

		# Draw the top hline
		if drawTopHLine:
			topNodes = [prevLine, self] if prevLine is not None else [self]
			HLine(topNodes).draw(window, startY, isTop = prevLine is None, isBottom = False)
			startY += 1

		for c in range(len(self.lines)):
			if isinstance(self.lines[c], LineBlock):
				startY = self.lines[c].draw(window, startY, prevLine = None if c <= 0 else self.lines[c-1], drawTopHLine = c > 0, drawBottomHLine = False)
			elif isinstance(self.lines[c], Line):
				# line protects itself
				self.lines[c].draw(window, startY)
				startY += 1
			else:
				raise UnknownElementException(self.lines[c])

		# Draw the bottom hline
		if drawBottomHLine:
			HLine([self]).draw(window, startY, isTop = False, isBottom = True)
			startY += 1

		return startY


	# Needed for HLine compatibility
	def getTopColWidths(self):
		return self.lines[0].getTopColWidths()

	def getTopContentLen(self):
		return len(self.getTopColWidths()) - self.node.depth + 1

	def getBottomColWidths(self):
		return self.lines[-1].getBottomColWidths()

	def getBottomContentLen(self):
		return len(self.getBottomColWidths()) - len(self.node._colWidths) + 1
