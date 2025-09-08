from .dataModel import DataModel
from .chars import Chars
from .scrollableWindow import ScrollableWindow
import curses

def printable(*args):
	return ' '.join([str(arg) for arg in args])

def _showTable(df, countableCols, hiddenCols, scr):
	w, h = curses.COLS, curses.LINES-2

	win = curses.newwin(h, w)
	statusWin = curses.newwin(1, w, h, 0)

	win.keypad(True)
	win.idcok(False)
	win.idlok(False)
	statusWin.idcok(False)
	statusWin.idlok(False)

	scrollWindow = ScrollableWindow(win)


	Chars.initColors()
	dataModel = DataModel(df, countableCols, hiddenCols, w)

	lines = []
	while True:
		# Rerender
		lines = dataModel.render()

		win.erase()
		scrollWindow.drawAll([line[0] for line in lines])

		ch = win.getch()

		if ch == ord('q'):
			break

		# Action
		focusedNode = None
		if ch == curses.KEY_UP:
			focusedNode = dataModel.focusNext(-1)
		elif ch == curses.KEY_DOWN:
			focusedNode = dataModel.focusNext(1)
		elif ch == curses.KEY_SR:
			scrollWindow.scrollUp()
		elif ch == curses.KEY_SF:
			scrollWindow.scrollDown()
		elif ch == curses.KEY_NPAGE:
			scrollWindow.scrollDown(20)
		elif ch == curses.KEY_PPAGE:
			scrollWindow.scrollUp(20)
		elif ch == curses.KEY_ENTER or ch == ord('\n') or ch == ord('\r') or ch == ord('o'):
			dataModel.click()
		else:
			statusWin.erase()
			statusWin.addstr(0, 0, printable('Unknown input:', ch))
			statusWin.refresh()
			continue

		# If a new node has been focused, find its coresponding line and scroll to it
		if focusedNode is not None:
			for y in range(len(lines)):
				if lines[y][1] == focusedNode:
					scrollWindow.scrollIntoView(y)
					break


def showTable(df, countableCols = [], hiddenCols = []):
	curses.wrapper(lambda scr: _showTable(df, set(countableCols), set(hiddenCols), scr))
