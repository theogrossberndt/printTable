import curses

class Chars:
	USE_CURSES = True

	DOWN_ARROW = '\u25bc'
	UP_ARROW = '\u25b2'

	WALL = '\u2502'

	contentSep = None
	singleHLineSep = None

	headerDecorator = None

	@staticmethod
	def initColors():
		if not Chars.USE_CURSES:
			Chars.headerDecorator = Chars.colorize(Style.BRIGHT, Fore.BLUE)
			return
		# Header
		curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
		Chars.headerDecorator = Chars.colorize(1, curses.A_BOLD)

		# Focused group
		curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
		# Unfocused group
		curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)


	@staticmethod
	def groupDecorator(isFocused):
		if Chars.USE_CURSES:
			return Chars.colorize(2 if isFocused else 3, curses.A_BOLD, curses.A_ITALIC if isFocused else 0)

		focused = [Style.BRIGHT, Fore.BLACK, Back.WHITE]
		unfocused = [Style.BRIGHT, Fore.WHITE, Back.BLACK]
		return Chars.colorize(*(focused if isFocused else unfocused))

	@staticmethod
	def colorize(*args):
		if Chars.USE_CURSES:
			res = curses.color_pair(args[0])
			for c in args[1:]:
				res |= c
			return lambda: res

		colorizeFn = lambda val: ''.join(args) + str(val) + Style.RESET_ALL
		return colorizeFn


	@staticmethod
	def color(val, *args):
		pass


	@staticmethod
	def colNameCleanup(v):
		if isinstance(v, str):
			subIdx = v.find('_')
			if subIdx > 0:
				return v[subIdx+1:]
			return v

		return [Chars.colNameCleanup(val) for val in v]


class SepClass:
	def __init__(self, startWall, centerWall, endWall, space, tr = ' ', br = ' ', tl = ' ', bl = ' ', hTop = ' ', hBottom = ' ', eSpace = ' ', eCenter = Chars.WALL, padding = 1):
		self.startWall = startWall
		self.centerWall = centerWall
		self.endWall = endWall
		self.space = space
		self.eSpace = eSpace
		self.eCenter = eCenter
		self.padding = padding

		self.tr = tr
		self.br = br
		self.tl = tl
		self.bl = bl
		self.hTop = hTop
		self.hBottom = hBottom


	@staticmethod
	def reversable(c1, c2, l1, l2):
		return SepClass.reverseIdx(c1, c2, l1, l2, [True, True])
#		return (c1 in l1 and c2 in l2) or (c1 in l2 or c2 in l1)


	@staticmethod
	def reverseIdx(c1, c2, l1, l2, out):
		if c1 in l1 and c2 in l2:
			return out[0]
		if c2 in l1 and c1 in l2:
			return out[1]
		return False


	def eSpaceLookup(self, topChar, bottomChar):
		match = SepClass.reverseIdx(topChar, bottomChar, [self.startWall], [self.eSpace], [self.tr, self.br])
		if match:
			return match

		match = SepClass.reverseIdx(topChar, bottomChar, [self.centerWall], [self.eSpace], [self.hTop, self.hBottom])
		if match:
			return match

		match = SepClass.reverseIdx(topChar, bottomChar, [self.endWall], [self.eSpace], [self.tl, self.bl])
		if match:
			return match

		if self.space in [topChar, bottomChar]:
			return self.space
		if self.eCenter in [topChar, bottomChar]:
			return self.eCenter

		return '!'


TOP_START = '\u250C'
TOP_MID = '\u252C'
TOP_END = '\u2510'

BOTTOM_START = '\u2514'
BOTTOM_MID = '\u2534'
BOTTOM_END = '\u2518'

MID_START = '\u251C'
MID_MID = '\u253C'
MID_END = '\u2524'

MID = '\u2500'

# Single line
SINGLE_SEP = {
	'MID': '\u2500',
	'MID_START': '\u251C',
	'MID_END': '\u2524',
	'TOP_MID': '\u252C',
	'BOTTOM_MID': '\u2534',
	'MID_MID': '\u253C',
	'BOTTOM_START': '.',
	'TOP_START': '^',
}

# Double line
DOUBLE_SEP = {
	'MID': '\u2550',
	'MID_START': '\u255E',
	'MID_END': '\u2561',
	'TOP_MID': '\u2564',
	'BOTTOM_MID': '\u2567',
	'MID_MID': '\u256A',
	'BOTTOM_START': '.',
	'TOP_START': '^',
}

# Heavy line
HEAVY_SEP = {
	'MID': '\u2501',
	'MID_START': '\u251D',
	'MID_END': '\u2525',
	'TOP_MID': '\u252F',
	'BOTTOM_MID': '\u2537',
	'MID_MID': '\u253F',
	'BOTTOM_START': '.',
	'TOP_START': '^',
}

Chars.contentSep = SepClass(Chars.WALL, Chars.WALL, Chars.WALL, ' ')

Chars.singleHLineSep = SepClass(
	startWall = '\u251c',
	centerWall = '\u253c',
	endWall = '\u2524',
	space = '\u2500',
	tr = '\u2514',
	tl = '\u2518',
	br = '\u250c',
	bl = '\u2510',
	hTop = '\u2534',
	hBottom = '\u252c'
)

Chars.heavyHLineSep = SepClass(
	startWall = '\u251d',
	centerWall = '\u253f',
	endWall = '\u2525',
	space = '\u2501',
	tr = '\u2515',
	tl = '\u2519',
	br = '\u250d',
	bl = '\u2511',
	hTop = '\u2537',
	hBottom = '\u252f'
)
