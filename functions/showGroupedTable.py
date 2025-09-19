from ..data import Tree
from ..drawing import ScrollableWindow
from ..keys import Keys

import curses
import pyperclip


def printable(*args):
	return ' '.join([str(arg) for arg in args])

def getHelpStr(maxW):
	quit = 'q: quit'
	copy = 'c: copy'
	hide = 'h: hide'
	enter = '[enter]: expand/collapse cell'
	nav = '[arrow keys]: navigate cells'
	scroll = '[shift up/down]: scroll window'
	page = '[page up/down]: jump 10 rows'
	keys = [quit, copy, hide, enter, nav, page, scroll]
	breakIndex = len(keys)
	helpStrs = []
	while len(keys) > 0:
		if breakIndex < 0:
			helpStrs.append(keys[0][:maxW])
			keys[0] = keys[0][maxW:]
			breakIndex = len(keys)
		subKeys = keys[:breakIndex]
		helpString = '    '.join(subKeys)
		if len(helpString) > maxW:
			breakIndex -= 1
		else:
			helpStrs.append(helpString)
			keys = keys[breakIndex:]
	return helpStrs


def showHelp(win):
	maxY, maxX = win.getmaxyx()
	win.erase()
	helpStrs = getHelpStr(maxX-3)
	for c in range(len(helpStrs)):
		win.addstr(c, 0, helpStrs[c].center(maxX-1, ' '), curses.A_REVERSE | curses.A_BOLD)
	win.refresh()


def setupWindows(scr):
	h, w = scr.getmaxyx()

	helpLineCount = len(getHelpStr(w-3))
	helpWin = scr.derwin(helpLineCount, w, h-helpLineCount, 0)
	showHelp(helpWin)

	statusWin = scr.derwin(1, w, 0, 0)
	statusWin.bkgd(' ', curses.color_pair(0) | curses.A_REVERSE | curses.A_BOLD)

	win = scr.derwin(h-helpLineCount-1, w, 1, 0)

	win.keypad(True)
	win.idcok(False)
	win.idlok(False)
	statusWin.idcok(False)
	statusWin.idlok(False)

	return (helpWin, statusWin, win)


def _showGroupedTable(tree, scr):
	# Window initiation stuff
	curses.raw()
	curses.curs_set(0)

	helpWin, statusWin, win = setupWindows(scr)

	scrollWindow = ScrollableWindow(win)
	focusNode = tree.root.children[0]
	focusNode.focusIn(focusNode.depth)

	Keys.initKeys()

	while True:
		# Rerender
		lineBlock = tree.render()

		scrollWindow.erase()
		scrollWindow.drawAll(lineBlock)

		statusWin.erase()
		statusWin.addstr(0, 2, str(focusNode))
		statusWin.refresh()

		ch = win.getch()

		if ch == ord('q'):
			break
		if ch == curses.KEY_RESIZE:
			scr.erase()
			helpWin, statusWin, win = setupWindows(scr)
			scrollWindow.setWindow(win)
			scr.refresh()
			continue

		# Focus management keys
		scroll = False
		if ch == Keys.UP:
			focusNode = focusNode.focusUp()
			scroll = True
		elif ch == Keys.DOWN:
			focusNode = focusNode.focusDown()
			scroll = True
		elif ch == Keys.LEFT:
			focusNode = focusNode.focusLeft()
			scroll = True
		elif ch == Keys.RIGHT:
			focusNode = focusNode.focusRight()
			scroll = True

		# Scroll management keys
		elif ch == Keys.S_UP:
			scrollWindow.scrollUp()
		elif ch == Keys.S_DOWN:
			scrollWindow.scrollDown()
		elif ch == Keys.PG_DOWN:
			# TODO: Make this better so its always about the same number of rows
			# Rn this scrolls 10 nodes, but a node might be 2 rows, or it might be 30
			for _ in range(10):
				focusNode = focusNode.focusDown()
			scroll = True
		elif ch == Keys.PG_UP:
			for _ in range(10):
				focusNode = focusNode.focusUp()
			scroll = True

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
			scrollWindow.scrollIntoView(yTop, yBottom)


def showGroupedTable(tree: Tree):
	curses.wrapper(lambda scr: _showGroupedTable(tree, scr))
