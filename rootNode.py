import pandas as pd
from .node import Node
from .line import Line
from .hline import HLine

class RootNode(Node):
	def __init__(self, inDf: pd.DataFrame):
		super().__init__(inDf, '', [], 1, None)

		# Remove the first element of the first line (group name doesn't exist for the root)
		self.firstLine = self.firstLine[1:]


	def render(self):
		inLines = super().render()

		# Merge neighboring hlines
		lines = []
		pendingHLine = None
		for line in inLines:
			if isinstance(line, HLine):
				if pendingHLine is None:
					pendingHLine = line
				else:
					pendingHLine = pendingHLine.merge(line)
			elif isinstance(line, Line):
				if pendingHLine is not None:
					lines.append(pendingHLine)
					pendingHLine = None
				lines.append(line)

		if pendingHLine is not None:
			lines.append(pendingHLine)

		return lines
