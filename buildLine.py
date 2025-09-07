from .chars import Chars, SepClass

class CursesStr:
	# decorator is a function or None for backwards compatibility reasons :(
	def __init__(self, x, strVal, decorator = None):
		self.x = x
		self.strVal = strVal
		self.decorator = decorator

	def draw(self, win, y):
		if self.decorator is None:
			win.addstr(y, self.x, self.strVal)
		else:
			win.addstr(y, self.x, self.strVal, self.decorator())

	def __str__(self):
		if isinstance(self.decorator, int):
			return self.strVal + ' ' + str(self.decorator)
		return self.strVal
#		return self.strVal[:10] + ' ' + str(self.decorator)


class Line:
	@staticmethod
	def leftFill(arr, l, fillVal):
		while len(arr) < l:
			arr.insert(0, fillVal)

	@staticmethod
	def buildCursesLine(content, colWidths, screenWidth, padding = 1, sepClass = Chars.contentSep, decorator = None, toStr = str, stretch = True, fwDecorator = None):
		elDecorators = []
		fillDecorator = None
		if decorator is not None and callable(decorator):
			fillDecorator = decorator
		elif decorator is not None and isinstance(decorator, list):
			elDecorators = [*decorator]


		start = sepClass.eCenter if len(colWidths) > len(content) else sepClass.startWall

		# Left fill content with empty strings to match the size of colWidths
		fwContent = [*content]
		Line.leftFill(fwContent, len(colWidths), '')

		# Left fill elDecorators with the fill decorator to match content size, and identity to match colWidths
		Line.leftFill(elDecorators, len(content), fillDecorator)
		Line.leftFill(elDecorators, len(colWidths), None)

		cursesLine = [CursesStr(0, start, fwDecorator)]
		strLen = len(start)

		for c in range(len(colWidths)):
			useE = len(colWidths)-c > len(content)
			useStart = len(colWidths)-c == len(content)
			center = sepClass.eCenter if useE else (sepClass.startWall if useStart else sepClass.centerWall)
			space = sepClass.eSpace if useE else sepClass.space

			el = toStr(fwContent[c])
			if c != 0:
				cursesLine.append(CursesStr(strLen, center, fwDecorator))
				strLen += len(center)

			cursesLine.append(CursesStr(strLen, space * padding, fwDecorator))
			strLen += padding

			cursesLine.append(CursesStr(strLen, el + (space * (colWidths[c] - len(el))), elDecorators[c]))
			strLen += colWidths[c]

			cursesLine.append(CursesStr(strLen, space * padding, fwDecorator))
			strLen += padding

		# expand the last column to match the screen width if we are stretching
		if stretch:
			diff = screenWidth - strLen - len(sepClass.endWall)
			cursesLine.append(CursesStr(strLen, sepClass.space * diff, elDecorators[-1]))
			strLen += diff

		cursesLine.append(CursesStr(strLen, sepClass.endWall, fwDecorator))
		return [cursesLine]


	@staticmethod
	def buildLine(content, colWidths, screenWidth, padding = 1, sepClass = Chars.contentSep, dry = False, decorator = None, toStr = str, stretch = True, fwDecorator = lambda v: v):
		elDecorators = []
		fillDecorator = None
		if decorator is not None and callable(decorator):
			fillDecorator = decorator
		elif decorator is not None and isinstance(decorator, list):
			elDecorators = [*decorator]


		start = sepClass.eCenter if len(colWidths) > len(content) else sepClass.startWall
		if not dry:
			# Left fill content with empty strings to match the size of colWidths
			fwContent = [*content]
			Line.leftFill(fwContent, len(colWidths), '')

			# Left fill elDecorators with the fill decorator to match content size, and identity to match colWidths
			Line.leftFill(elDecorators, len(content), fillDecorator)
			Line.leftFill(elDecorators, len(colWidths), lambda v: v)

			lineStr = fwDecorator(start)

		strLen = len(start)

		for c in range(len(colWidths)):
			useE = len(colWidths)-c > len(content)
			useStart = len(colWidths)-c == len(content)
			center = sepClass.eCenter if useE else (sepClass.startWall if useStart else sepClass.centerWall)
			space = sepClass.eSpace if useE else sepClass.space

			el = toStr(fwContent[c])
			if c != 0:
				strLen += len(center)
				lineStr += fwDecorator(center)
			effElDecorator = elDecorators[c] if elDecorators[c] is not None else lambda v: v
			lineStr += fwDecorator(space * padding) + effElDecorator(el)
			lineStr += fwDecorator(space * (colWidths[c] - len(el) + padding))
			strLen += 2*padding + colWidths[c]

		strLen += len(sepClass.endWall)
		if dry:
			return strLen

		# expand the last column to match the screen width if we are stretching
		if stretch:
			diff = screenWidth - strLen
			lineStr += fwDecorator(sepClass.space * diff)

		lineStr += fwDecorator(sepClass.endWall)
		return [lineStr]
