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


	def drawAll(self, lines: LineBlock):
#		self.contentLen = len(lines)
#		for y in range(self.contentLen):
#			effY = y-self.top
#			if effY < 0 or effY > self.h:
#				continue
#			try:
#				if isinstance(lines[y], Line):
#					lines[y].draw(self.win, effY)
#				elif isinstance(lines[y], HLine):
#					lines[y].draw(self.win, effY, isTop = y == 0, isBottom = y == self.contentLen-1)
#			except curses.error:
#				pass
#			except Exception as e:
#				exceptionStr = str(e)
#				self.win.addstr(effY, 0, exceptionStr[:min(len(exceptionStr), self.w)])
		self.contentLen = lines.draw(self.win, y = -1 * self.top) + self.top


	def scrollTo(self, y):
		self.top = y
		self.top = min(self.top, self.contentLen-self.h)
		self.top = max(self.top, 0)


	def scrollDown(self, step = 1):
		self.scrollTo(self.top + step)


	def scrollUp(self, step = 1):
		self.scrollTo(self.top - step)


	def scrollIntoView(self, lineYTop, lineYBottom, behavior = MIN_SCROLL):
		winMin = self.top
		winMax = self.top + self.h

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
