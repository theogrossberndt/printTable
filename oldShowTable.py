from .rootNode import RootNode
from .node import Node
from .chars import Chars
from .scrollableWindow import ScrollableWindow
import curses
from .config import Config
from .line import Line
import pyperclip


def printable(*args):
	return ' '.join([str(arg) for arg in args])


def _showTable(df, countableCols, hiddenCols, scr):
	# Window initiation stuff
	w, h = curses.COLS, curses.LINES-2

	win = curses.newwin(h, w)
	statusWin = curses.newwin(1, w, h, 0)

	win.keypad(True)
	win.idcok(False)
	win.idlok(False)
	statusWin.idcok(False)
	statusWin.idlok(False)
	curses.curs_set(0)

	scrollWindow = ScrollableWindow(win)

	root = RootNode(Config(df, countableCols, hiddenCols))
	focusNode = root.children[0]
	focusNode.focusIn(focusNode.depth)

	lines = []
	while True:
		# Rerender
		lines = root.render()

		win.erase()
		scrollWindow.drawAll(lines)

		statusWin.erase()
		statusWin.addstr(0, 0, str(focusNode))
		statusWin.refresh()

		ch = win.getch()

		if ch == ord('q'):
			break

		# Focus management keys
		scroll = False
		if ch == curses.KEY_UP:
			focusNode = focusNode.focusUp()
			scroll = True
		elif ch == curses.KEY_DOWN:
			focusNode = focusNode.focusDown()
			scroll = True
		elif ch == curses.KEY_LEFT:
			focusNode = focusNode.focusLeft()
			scroll = True
		elif ch == curses.KEY_RIGHT:
			focusNode = focusNode.focusRight()
			scroll = True

		# Scroll management keys
		elif ch == curses.KEY_SR:
			scrollWindow.scrollUp()
		elif ch == curses.KEY_SF:
			scrollWindow.scrollDown()
		elif ch == curses.KEY_NPAGE:
			scrollWindow.scrollDown(20)
		elif ch == curses.KEY_PPAGE:
			scrollWindow.scrollUp(20)

		elif ch == ord('c'):
			pyperclip.copy(str(focusNode))

		elif ch == ord('h'):
			focusNode.handleKey(Node.HIDE)
			focusNode = focusNode.focusDown()
		elif ch == curses.KEY_ENTER or ch == ord('\n') or ch == ord('\r') or ch == ord('o'):
			focusNode.handleKey(Node.CLICK)
		else:
			statusWin.erase()
			statusWin.addstr(0, 0, printable('Unknown input:', ch))
			statusWin.refresh()
			continue

		if scroll:
			# Find the relevant line number
			for y in range(len(lines)):
				if isinstance(lines[y], Line) and focusNode in lines[y].parents:
					scrollWindow.scrollIntoView(y)
					break


def showTable(df, countableCols = [], hiddenCols = []):
	curses.wrapper(lambda scr: _showTable(df, set(countableCols), set(hiddenCols), scr))
