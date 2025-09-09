from .chars import Chars, SepClass
from .buildLine import Line, CursesStr

class ExpandableLines:
	def __init__(self, minifiedLine, staticLines, childLines, node):
		self.minifiedLine = minifiedLine	# [StaticLines | HLine]
		self.staticLines = staticLines		# [StaticLines | HLine]
		self.childLines = childLines		# [ExpandableLines] | []
		self.node = node					# ExpandableNode

	# Always returns a list of static lines
	def render(self):
		out = []
		if not self.node.expanded:
#			print(int(self.node.isFocused), len(self.minifiedLine), len(self.minifiedLine[0]))
			out = self.minifiedLine[int(self.node.isFocused)]
		else:
			if self.staticLines is not None:
				out.extend(self.staticLines[int(self.node.isFocused)])

			renderedChildren = []
			for childLine in self.childLines:
				renderedChildren.extend(childLine.render())

			out.extend(renderedChildren)
		return [el if isinstance(el, tuple) else (el, self.node) for el in out]


class StaticLines:
	def __init__(self, content, colWidths, screenWidth, bottomColWidths = None, **kwargs):
		self.content = content
		## TODO: Can I delete these?
		self.topColWidths = colWidths
		self.bottomColWidths = colWidths if bottomColWidths is None else bottomColWidths

		self.topColCount = len(content)
		self.bottomColCount = len(content)

		if 'cursesReps' in kwargs:
			self.cursesReps = kwargs['cursesReps']
		else:
			self.cursesReps = Line.buildCursesLine(content, colWidths, screenWidth, **kwargs)

	def extend(self, other):
		self.cursesReps.extend(other.cursesReps)
		self.bottomColWidths = other.bottomColWidths
		self.bottomColCount = other.bottomColCount

	def copy(self):
		return StaticLines(self.content, self.topColWidths, 0, self.bottomColWidths, cursesReps = self.cursesReps)


class HLine:
	def __init__(self, colCount, screenWidth, **kwargs):
		self.kwargs = {'sepClass': Chars.singleHLineSep, **kwargs}
		self.colCount = colCount if isinstance(colCount, list) else [colCount, colCount]
		self.screenWidth = screenWidth

		if 'cursesRep' in self.kwargs:
			self.cursesRep = self.kwargs['cursesRep']
			del self.kwargs['cursesRep']
		else:
			self.cursesRep = None

	def copy(self):
		return HLine(self.colCount, self.screenWidth, cursesRep = self.cursesRep, **self.kwargs)

	def extend(self, other):
		self.colCount[-1] = other.colCount[-1]

	# Takes in two StaticLines or None
	def consolidate(self, topLine, bottomLine):
		fwDecorator = self.kwargs.pop('fwDecorator', None)
		self.kwargs.pop('decorator', None)

		# Merge the top and bottom lines into one using the bottomCols of the top and topCols of the bottom
		topStr = Line.buildLine([''] * self.colCount[0], topLine.bottomColWidths, self.screenWidth, **self.kwargs)[0] if topLine is not None else ''
		bottomStr = Line.buildLine([''] * self.colCount[1], bottomLine.topColWidths, self.screenWidth, **self.kwargs)[0] if bottomLine is not None else ''

		outStr = ''
		sep = self.kwargs['sepClass']
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
		self.cursesRep = [CursesStr(0, outStr, fwDecorator)]


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
#		return '*'
