from .line import Line
from .hline import HLine
from .blockLine import LineBlock

import curses

class ScrollableWindow:
	MIN_SCROLL = 0
	CENTER = 1

	def __init__(self, win):
		self.win = win
		self.h, self.w = self.win.getmaxyx()
		self.contentLen = 0
		self.top = 0


	def setWindow(self, window):
		self.win = window
		self.h, self.w = self.win.getmaxyx()


	def drawAll(self, lines: LineBlock):
		lines.draw(self, y = 0)

	def erase(self):
		self.contentLen = 0
		self.win.erase()


	def getmaxyx(self):
		return self.win.getmaxyx()


	def addstr(self, y, x, string, *args):
		self.contentLen = max(self.contentLen, y+1)
		effY = y - self.top
		if effY >= 0 and effY < self.h:
			# Check for widths now
			if x + len(string) >= self.w:
				string = string[:self.w - x - 1]
			self.win.addstr(effY, x, string, *args)


	def getch(self):
		return self.win.getch()


	def scrollTo(self, y):
		self.top = y
		self.top = min(self.top, self.contentLen-self.h)
		self.top = max(self.top, 0)


	def scrollDown(self, step = 1):
		self.scrollTo(self.top + step)


	def scrollUp(self, step = 1):
		self.scrollTo(self.top - step)


	def scrollIntoView(self, lineYTop, lineYBottom = None, behavior = MIN_SCROLL):
		winMin = self.top
		winMax = self.top + self.h
		lineYBottom = lineYBottom if lineYBottom is not None else lineYTop

		# If the line is already in view, theres nothing to do
		if lineYTop >= winMin and lineYBottom < winMax - 2:
			return

		# If the behavior is min scroll put lineY to either the top (if its above the current win), or the bottom (if below)
		if behavior == ScrollableWindow.MIN_SCROLL:
			if lineYTop < winMin:
				self.scrollTo(lineYTop)
			else:
				self.scrollTo(lineYBottom - self.h + 1)

		# If the behavior is center, put attempt to put lineY in the center of the window
		if behavior == ScrollableWindow.CENTER:
			linesAbove = int(self.h / 2)
			sectionCenter = int((lineYTop + lineYBottom)/2)
			self.scrollTo(sectionCenter - linesAbove)
