from ..drawing import ScrollableWindow
import curses

def _printLine(window, y, string, isFocused, isSelected, *args):
	window.addstr(y, 0, '[', curses.A_BOLD)
	if isSelected:
		window.addstr(y, 1, '\u2714', curses.color_pair(1) | curses.A_BOLD | (curses.A_REVERSE if isFocused else 0))
	else:
		window.addstr(y, 1, ' ', curses.A_REVERSE if isFocused else 0)
	window.addstr(y, 2, ']', curses.A_BOLD)
	window.addstr(y, 3, ' ' + str(string), *args)


def drawEnter(window, isFocused, enterStr = 'Continue'):
	maxY, maxX = window.getmaxyx()
	x = int((maxX-len(enterStr))/2)

	if isFocused:
		window.bkgd(' ', curses.color_pair(3))
	else:
		window.bkgd(' ', curses.color_pair(0))

	window.erase()
	window.border()
	window.addstr(1, x, enterStr, curses.A_BOLD)
	window.refresh()


def _showSelectableList(scr, options, multiselection = False, header = None, allowAll = True):
	# Window initiation stuff
	curses.curs_set(0)
	w, h = curses.COLS, curses.LINES

	headerH = 4 if header is not None else 0
	topH = 1 + headerH

	instructionWin = curses.newwin(topH, w)
	instructionWin.idcok(False)
	instructionWin.idlok(False)
	if header is not None:
		instructionWin.addstr(0, 0, ' '.center(w-1, ' '), curses.A_REVERSE | curses.A_BOLD)
		instructionWin.addstr(1, 0, str(header).center(w-1, ' '), curses.A_REVERSE | curses.A_BOLD)
		instructionWin.addstr(2, 0, ' '.center(w-1, ' '), curses.A_REVERSE | curses.A_BOLD)

	if multiselection:
		instructionWin.addstr(headerH, 1, 'Please select one or more of the following options:')
	else:
		instructionWin.addstr(headerH, 1, 'Please select one of the following options:')
	instructionWin.refresh()

	curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
	curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)


	bottomH = 5
	enterW = len('   Continue   ')
	enterWin = curses.newwin(3, enterW, h-bottomH, int(w/2-enterW/2))
	drawEnter(enterWin, False)

	bottomWin = curses.newwin(1, w, h-1, 0)
	bottomWin.addstr(0, 0, 'Use the arrow keys to focus, the enter key to toggle an option, and shift arrows to toggle between sections'.center(w-1, ' '), curses.A_REVERSE | curses.A_BOLD)
	bottomWin.refresh()

	win = curses.newwin(h - topH - bottomH, w-4, topH, 2)

	win.keypad(True)
	win.idcok(False)
	win.idlok(False)

	window = ScrollableWindow(win)

	cursorIdx = 0
	selected = set()

	useAllOption = allowAll and multiselection
	onEnter = False
	while True:
		# Rerender
		window.erase()

		if useAllOption:
			_printLine(window, 0, 'All', cursorIdx == 0 and not onEnter, len(selected) == len(options), curses.A_BOLD)

		for c in range(len(options)):
			y = c+1 if useAllOption else c
			_printLine(window, y, options[c], cursorIdx == y and not onEnter, c in selected)

		ch = window.getch()

		if ch == curses.KEY_UP:
			cursorIdx -= 1
		elif ch == curses.KEY_DOWN:
			cursorIdx += 1
		elif ch == curses.KEY_SR or ch == curses.KEY_SF:
			onEnter = not onEnter
			drawEnter(enterWin, onEnter)
		elif ch == curses.KEY_ENTER or ch == ord('\n') or ch == ord('\r'):
			if not onEnter:
				optionIdx = cursorIdx-1 if useAllOption else cursorIdx
				# Can only happen if all is focused
				if optionIdx < 0:
					# If all are already selected, deselect all, otherwise select all
					if len(selected) == len(options):
						selected = set()
					else:
						selected = set(range(len(options)))
				else:
					if optionIdx in selected:
						selected.discard(optionIdx)
					elif multiselection:
						selected.add(optionIdx)
					else:
						selected = {optionIdx}
			else:
				break

		# Wrap cursorIdx
		effLen = len(options) + (1 if useAllOption else 0)
		cursorIdx = (cursorIdx + effLen) % effLen
		window.scrollIntoView(cursorIdx)

	return selected


def showSelectableList(*args, **kwargs):
	return curses.wrapper(lambda scr: _showSelectableList(scr, *args, **kwargs))
