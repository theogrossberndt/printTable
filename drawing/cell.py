import curses

class _CellChars:
	def __init__(self, start, space, padding):
		self.start = start
		self.space = space
		self.padding = padding


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
			repVal = val[:maxX - startX-1]
			if isContent:
				repVal = repVal[:-3] + '...'
			window.addstr(y, startX, repVal, decorator)
		return startX + len(val)

	def draw(self, window: curses.window, y: int, startX: int, elDecorator: int, fwDecorator: int, cellChars: _CellChars, maxX: int):
		startX = self._drawStr(window, y, startX, cellChars.start, fwDecorator, maxX)	# Left separator
		startX = self._drawStr(window, y, startX, cellChars.space * cellChars.padding, fwDecorator, maxX)	# Left padding
		startX = self._drawStr(window, y, startX, self.content, elDecorator | fwDecorator, maxX, True)	# Content
		startX = self._drawStr(window, y, startX, cellChars.space * (self.colWidth - len(self.content)), elDecorator | fwDecorator, maxX)	# Remaining col space
		startX = self._drawStr(window, y, startX, cellChars.space * cellChars.padding, fwDecorator, maxX)	# Right padding
		return startX
