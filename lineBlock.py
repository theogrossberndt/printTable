from typing import List, Union
import curses

# A line block is a collection of lines or other line blocks that represent a conceptually connected chunk of lines
# This connection might be belonging to the same node, or belonging to the same data line in the case of lines that overflow their column
class LineBlock:
	def __init__(self):
		self.lines: List[Union[Line, LineBlock]] = []

	def addLine(self, line: Union[Line, LineBlock]):
		self.lines.append(line)

	def draw(self, window: curses.window, y: int = 0) -> int:
		startY = y
		for line in self.lines:
			if isinstance(line, LineBlock):
				startY = line.draw(window, startY)
			elif isinstance(line, Line):
				line.draw(window, startY)
				startY += 1
		return startY
