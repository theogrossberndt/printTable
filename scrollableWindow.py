from .lineBuilder import LineBuilder
from .hline import HLine
import curses

class ScrollableWindow:
	MIN_SCROLL = 0
	CENTER = 1

	def __init__(self, win):
		self.win = win
		self.h, self.w = self.win.getmaxyx()
		self.contentLen = 0
		self.top = 0


	def drawAll(self, lines):
		self.contentLen = len(lines)
		for y in range(self.contentLen):
			effY = y-self.top
			if effY < 0 or effY > self.h:
				continue
			try:
				if isinstance(lines[y], LineBuilder):
					lines[y].draw(self.win, effY)
				elif isinstance(lines[y], HLine):
					lines[y].draw(self.win, effY, isTop = y == 0, isBottom = y == self.contentLen-1)
			except curses.error:
				pass
			except Exception as e:
				exceptionStr = str(e)
				self.win.addstr(effY, 0, exceptionStr[:min(len(exceptionStr), self.w)])


	def scrollTo(self, y):
		self.top = y
		self.top = min(self.top, self.contentLen-self.h)
		self.top = max(self.top, 0)


	def scrollDown(self, step = 1):
		self.scrollTo(self.top + step)


	def scrollUp(self, step = 1):
		self.scrollTo(self.top - step)


	def scrollIntoView(self, lineY, behavior = MIN_SCROLL):
		winMin = self.top
		winMax = self.top + self.h

		# If the line is already in view, theres nothing to do
		if lineY >= winMin and lineY < winMax - 2:
			return

		# If the behavior is min scroll put lineY to either the top (if its above the current win), or the bottom (if below)
		if behavior == ScrollableWindow.MIN_SCROLL:
			if lineY < winMin:
				self.scrollTo(lineY)
			else:
				self.scrollTo(lineY - self.h + 2)

		# If the behavior is center, put attempt to put lineY in the center of the window
		if behavior == ScrollableWindow.CENTER:
			linesAbove = int(self.h / 2)
			self.scrollTo(lineY - linesAbove)
