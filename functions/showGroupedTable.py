from ..data import Tree
from ..drawing import ScrollableWindow

import curses
import pyperclip


def printable(*args):
	return ' '.join([str(arg) for arg in args])


def _showGroupedTable(tree, scr):
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
	focusNode = tree.root.children[0]
	focusNode.focusIn(focusNode.depth)

	while True:
		# Rerender
		lineBlock = tree.render()

		win.erase()
		scrollWindow.drawAll(lineBlock)

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
			newFocusNode = focusNode.focusDown()
			scroll = True

			focusNode.hide()
			focusNode = newFocusNode
		elif ch == curses.KEY_ENTER or ch == ord('\n') or ch == ord('\r') or ch == ord('o'):
			focusNode.click()

		else:
			statusWin.erase()
			statusWin.addstr(0, 0, printable('Unknown input:', ch))
			statusWin.refresh()
			continue

		if scroll:
			yTop, yBottom = lineBlock.getNodeYRange(focusNode)
			scrollWindow.scrollIntoView(yTop + scrollWindow.top, yBottom + scrollWindow.top)


def showGroupedTable(tree: Tree):
	curses.wrapper(lambda scr: _showGroupedTable(tree, scr))
