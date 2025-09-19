import os
import curses

class Keys:
	@staticmethod
	def initKeys():
		if os.name == 'posix':
			Keys.S_UP = curses.KEY_SR
			Keys.S_DOWN = curses.KEY_SF
		else:
			Keys.S_UP = 547
			Keys.S_DOWN = 548
		Keys.PG_UP = curses.KEY_PPAGE
		Keys.PG_DOWN = curses.KEY_NPAGE
		Keys.UP = curses.KEY_UP
		Keys.DOWN = curses.KEY_DOWN
		Keys.LEFT = curses.KEY_LEFT
		Keys.RIGHT = curses.KEY_RIGHT
