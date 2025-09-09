import pandas as pd
from .hline import HLine
from .line import Line
from .chars import Chars
from typing import List
import curses

class Node:
	def __init__(self, inDf: pd.DataFrame, groupName: str, colWidths: List[int], depth: int, parent):
		self.parent = parent
		self.depth = depth

		# colWidths is an accumulated list of all the column widths of the parents, with the last element being the width
		# of the __first column__ the current node is responsible for printing (group name)
		self.colWidths: List[int] = [*colWidths, 0]

		# The group name is the first content cell of the first line
		# It will be extended to steal the first child's first line once they are all built
		self.firstLine: List[str] = [groupName]

		self.isFocused = False

		# If inDf is none, this is a leaf node with it's only important value being the groupname
		# headerLabels will be taken care of by the parent
		if inDf is not None:
			# Remove any columns from the dataframe that are only na
			df: pd.DataFrame = inDf.dropna(axis=1, how='all')

			# The header labels will also be extended to steal the first child's
			self.headerLabels: List[str] = [Chars.colNameCleanup(df.columns[0])]

			self.children: List[node] = None

			self._createChildren(df)
			self._absorbFirstChild()

			self.topContentLen = self.children[0].topContentLen + 1
			self.topColWidths = self.children[0].topColWidths

			self.bottomContentLen = self.children[-1].bottomContentLen + 1
			self.bottomColWidths = self.children[-1].bottomColWidths

		else:
			# Remove the appended 0 from colWidths, this columns width is already calculated
			self.colWidths = self.colWidths[:-1]

			self.headerLabels = []
			self.children: List[node] = []

			self.topContentLen = 1
			self.topColWidths = self.colWidths

			self.bottomContentLen = 1
			self.bottomColWidths = self.colWidths


	# Iterates through the dataframe creating a child for each group and calculating the column size
	def _createChildren(self, df: pd.DataFrame):
		if self.children is not None:
			return

		self.children: List[Node] = []

		# The column name also needs to fit in the column, so add that
		myColWidth: int = len(self.headerLabels[0])

		# Group by the common column and iterate over the groups
		# However, if there is only a single column there is nothing to group
		# Iterate over the series adding each element as its own leaf node (a Node with None as the dataframe)
		groups: List(tuple) = []
		if len(df.columns) > 1:
			for groupName, group in df.groupby(df.columns[0]):
				# The groupname is the value of the first column, so all children should have this column be the same length
				# Calculate the max group name length to get the column width for this node
				# TODO: add definable tostr support perhaps
				myColWidth = max(len(str(groupName)), myColWidth)

				# Each group turns into its own node, but they all need the same colWidth which is not calculated yet
				# Delay creation until after all groups have been iterated through
				groups.append((groupName, group.drop(columns=df.columns[0])))
		else:
			series: pd.Series = df[df.columns[0]].astype(str)
			myColWidth = max(myColWidth, series.str.len().max())
			for val in series:
				groups.append((val, None))

		self.colWidths[-1] = myColWidth
		for groupName, group in groups:
			self.children.append(Node(group, groupName, self.colWidths, self.depth+1, self))


	# The first content line and the header labels line of the first child can be absorbed upwards
	# In order to render these the relevant colWidths will need to be obtained, which is also done recursively
	# Steal them from the child by clearing the child's so nothing gets double printed
	def _absorbFirstChild(self):
		if len(self.children) == 0:
			return

		# Because children are created via dfs traversal, this as already been done if possible to the child
		# Consequentially stealing the first child's first line will be the full first line
		child = self.children[0]
		self.firstLine.extend(child.firstLine)
		child.firstLine = []

		self.headerLabels.extend(child.headerLabels)
		child.headerLabels = []

		self.colWidths = [*child.colWidths]


	def render(self) -> List[Line]:
		# I need to render the headerLabels (column names) and my firstLine (group name, first line of first child)
		# Then render all children / leaf cells
		# firstLine and headerLabels might be empty lists if they were absorbed into a parent

		renderedLines: List[Line] = []
		renderedLines.extend(self._renderHeaderLabels())
		renderedLines.extend(self._renderFirstLine())

		# Only prepend an hline before the child starts if the first line was not absorbed
		# Otherwise there will be a line between the first and second lines weirdly
		if len(renderedLines) > 0:
			renderedLines.insert(0, HLine(self))

		for child in self.children:
			renderedLines.extend(child.render())

		renderedLines.append(HLine(self))

		return renderedLines


	def _renderHeaderLabels(self) -> List[Line]:
		if len(self.headerLabels) == 0:
			return []
		return [Line(self.headerLabels, self, lineType = Line.HEADER)]


	def _renderFirstLine(self) -> List[Line]:
		if len(self.firstLine) == 0:
			return []
		# TODO: First lines get dim sep lines above them
		return [Line(self.firstLine, self)]


	def __str__(self):
		return self.firstLine[0] if len(self.firstLine) > 0 else 'root'
