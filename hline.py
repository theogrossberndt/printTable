import curses
from .chars import Chars, SepClass
from .line import Line

class DummyWindow:
	def __init__(self, window):
		self.window = window
		self.string = ''


	def getmaxyx(self):
		return self.window.getmaxyx()


	def addstr(self, y, x, val, *args):
		lenDiff = (x + len(str(val))) - len(self.string)
		if lenDiff > 0:
			self.string += ' ' * lenDiff

		self.string = self.string[:x] + str(val) + self.string[x+len(str(val)):]

	def steal(self):
		ret = self.string
		self.string = ''
		return ret


class HLine:
	def __init__(self, nodes, sepClass = None, decorator = 0):
		self.nodes = nodes[:min(2, len(nodes))] if isinstance(nodes, list) else [nodes]
		self.sepClass = sepClass if sepClass is not None else Chars.singleHLineSep
		self.decorator = decorator

	def merge(self, other):
		# The shallowest node of each hline should be kept
		newNodes = [None, None]
		for node in self.nodes:
			if newNodes[0] is None or newNodes[0].depth > node.depth:
				newNodes[0] = node

		for node in other.nodes:
			if newNodes[1] is None or newNodes[1].depth > node.depth:
				newNodes[1] = node

		return HLine(newNodes, self.sepClass, self.decorator)


	def draw(self, window: curses.window, y, isTop = False, isBottom = False, sepClass = None):
		sep = sepClass if sepClass is not None else self.sepClass

		# Use a dummy window object to 'draw' the top and bottom lines
		# Instead it will be printing them to a string
		dummyWin = DummyWindow(window)

		if isTop:
			topNode = None
			bottomNode = self.nodes[0]
		elif isBottom:
			topNode = self.nodes[0]
			bottomNode = None
		else:
			topNode = self.nodes[0]
			bottomNode = self.nodes[1] if len(self.nodes) > 1 else None


		if topNode is not None:
			topLine = Line(['' for _ in range(topNode.bottomContentLen)], topNode, sepClass = sep, colWidths = topNode.bottomColWidths)
			topLine.draw(dummyWin, 0, False)
			topStr = dummyWin.steal()
		else:
			topStr = ''

		if bottomNode is not None:
			bottomLine = Line(['' for _ in range(bottomNode.topContentLen)], bottomNode, sepClass = sep, colWidths = bottomNode.topColWidths)
			bottomLine.draw(dummyWin, 0, False)
			bottomStr = dummyWin.steal()
		else:
			bottomStr = ''

		outStr = ''
		for c in range(max(len(topStr), len(bottomStr))):
			if c >= len(topStr):
				if bottomStr[c] == sep.startWall:
					outStr += sep.br
				elif bottomStr[c] == sep.centerWall:
					outStr += sep.hBottom
				elif bottomStr[c] == sep.endWall:
					outStr += sep.bl
				else:
					outStr += bottomStr[c]
			elif c >= len(bottomStr):
				if topStr[c] == sep.startWall:
					outStr += sep.tr
				elif topStr[c] == sep.centerWall:
					outStr += sep.hTop
				elif topStr[c] == sep.endWall:
					outStr += sep.tl
				else:
					outStr += topStr[c]
			else:
				outStr += self.combineChars(topStr[c], bottomStr[c], sep)
#		window.addstr(y, 0, topStr, self.decorator)
#		window.addstr(y, 0, bottomStr, self.decorator)
		window.addstr(y, 0, outStr, self.decorator)


	def combineChars(self, topChar, bottomChar, sep):
		# Matching characters are preserved
		if topChar == bottomChar:
			return topChar

		# Anything with an espace in it is complicated
		if topChar == sep.eSpace or bottomChar == sep.eSpace:
			return sep.eSpaceLookup(topChar, bottomChar)

		if SepClass.reversable(topChar, bottomChar, [sep.centerWall], [sep.startWall, sep.endWall, sep.eCenter]):
			return sep.centerWall

		if SepClass.reversable(topChar, bottomChar, [sep.startWall], [sep.endWall]):
			return sep.centerWall

		if (topChar == sep.eCenter and bottomChar not in [sep.eSpace, sep.space]):
			return bottomChar
		if (bottomChar == sep.eCenter and topChar not in [sep.eSpace, sep.space]):
			return topChar

		if topChar in [sep.startWall, sep.centerWall, sep.endWall, sep.eCenter] and bottomChar == sep.space:
			return sep.hTop
		if bottomChar in [sep.startWall, sep.centerWall, sep.endWall, sep.eCenter] and topChar == sep.space:
			return sep.hBottom
		return '(' + topChar + bottomChar + ')'
