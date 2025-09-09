import pandas as pd

from .chars import Chars
from .leafTable import LeafTable
from .printableLines import StaticLines, ExpandableLines, HLine

class ExpandableNode:
	def __init__(self, groupName, df, leftColWidths, countableCols, hiddenCols, screenWidth, parent):
		self.groupName = groupName
		self.firstColName = Chars.colNameCleanup(df.columns[0])
		self.children = []
		self.leafTables = []
		self.screenWidth = screenWidth
		self.parent = parent
		self.isFocused = False

		# Sum all countable columns
		self.columnSummary = 0
		for col in countableCols:
			if col in df.columns:
				self.columnSummary += pd.to_numeric(df[col].fillna(0), downcast='integer').sum()

		# Bare minimum width is the length of the column header
		self.myColWidth = len(self.firstColName)

		for subName, subTable in df.groupby(df.columns[0]):
			subName = str(subName)
			subTable.dropna(axis=1, how='all', inplace=True)

			if len(subTable) <= 1 or len(df.columns) == 1:
				# Leaf tables only take up the length of their entry in column 0
				self.myColWidth = max(self.myColWidth, len(subName))
				self.leafTables.append(subTable)
				continue

			# Remove the grouped column from the child tables and store them for creation later
			# Creating them after the first pass through allows us to figure out the column width in advance
			self.children.append((subName, subTable.drop(columns=df.columns[0])))

			# Non-leaves take up an additional 2 spaces for the drop down arrow and a space
			self.myColWidth = max(self.myColWidth, len(subName)+2)

		# Run through the children building each into its own node
		self.colWidths = [*leftColWidths, self.myColWidth]
		self.children = [ExpandableNode(*params, self.colWidths, countableCols, hiddenCols, self.screenWidth, self) for params in self.children]

		# If we have any leaf tables, combine them, group them by their column usage, and turn each into its own printable table
		if len(self.leafTables) > 0:
			leaves = pd.concat(self.leafTables)
			self.leafTables = []
			leaves['filledCols'] = leaves.notna().agg(lambda row: tuple(leaves.columns[row]), axis=1)
			self.leafTables = []
			for cols, subTable in leaves.groupby('filledCols'):
				self.leafTables.append(LeafTable(subTable[list(cols)], self.colWidths, countableCols, hiddenCols, self.screenWidth))

		# Initially, set all nodes to colapsed unless it only has a single child
#		self.expanded = len(self.children) + len(self.leafTables) == 1
		self.expanded = False


	def buildExpandedHeader(self, isFocused):
		# The expanded header consists of the expanded version of the group name followed by the first column, as this is a shared column among all sub tables
		# However, if we only have leaf tables then we will absorb the first leaf table header into our header
		if len(self.children) == 0:
			content = [Chars.UP_ARROW + ' ' + self.groupName, *self.leafTables[0].df.columns]
			decorators = [Chars.headerDecorator for _ in content]
			decorators[0] = Chars.groupDecorator(isFocused)
			colWidths = self.leafTables[0].colWidths
			headerLines = StaticLines(content, colWidths, self.screenWidth, decorator = decorators)
		else:
			content = [Chars.UP_ARROW + ' ' + self.groupName, self.firstColName, '']
			colWidths = [*self.colWidths, self.children[0].myColWidth]
			decorators = [Chars.groupDecorator(isFocused), Chars.headerDecorator, None]
			headerLines = StaticLines(content, colWidths, self.screenWidth, decorator = decorators)

		return [
			HLine(headerLines.topColCount, self.screenWidth, sepClass = Chars.heavyHLineSep),
			headerLines,
			HLine(headerLines.bottomColCount-1, self.screenWidth, sepClass = Chars.heavyHLineSep if len(self.leafTables) == 0 and len(self.children) > 1 else Chars.singleHLineSep)
		]


	def buildLeafLines(self):
		leafLines = []
		for leafTable in self.leafTables:
			# For the first leaf, only add the header if there are children, otherwise it has been absorbed already
			lines = leafTable.buildLines(addHeader = len(leafLines) > 0 or len(self.children) > 0)
			leafLines.append(HLine(lines.topColCount, self.screenWidth))
			leafLines.append(lines)
			leafLines.append(HLine(lines.bottomColCount, self.screenWidth))

		if len(self.leafTables) > 0:
			leafLines[-1] = HLine(leafLines[-2].bottomColCount, self.screenWidth, sepClass = Chars.heavyHLineSep)
		return leafLines


	def buildLines(self, addMine = True):
		leafLines = self.buildLeafLines()
		staticLines = [
			[*self.buildExpandedHeader(False), *leafLines],
			[*self.buildExpandedHeader(True), *leafLines]
		]

		builtChildren = [child.buildLines() for child in self.children]

		summaryStr = 'Total: ' + str(self.columnSummary)

		# The minified (unexpanded) representation of a child is just the group name with an hline
		unfocused = StaticLines([Chars.DOWN_ARROW + ' ' + self.groupName, summaryStr], self.colWidths, self.screenWidth, decorator = [Chars.groupDecorator(False), None])
		focused = StaticLines([Chars.DOWN_ARROW + ' ' + self.groupName, summaryStr], self.colWidths, self.screenWidth, decorator = [Chars.groupDecorator(True), None])

		minifiedUnfocused = [
			HLine(2, self.screenWidth, sepClass = Chars.heavyHLineSep),
			unfocused,
			HLine(2, self.screenWidth, sepClass = Chars.heavyHLineSep),
		]

		minifiedFocused = [
			HLine(2, self.screenWidth, sepClass = Chars.heavyHLineSep),
			focused,
			HLine(2, self.screenWidth, sepClass = Chars.heavyHLineSep),
		]

		return ExpandableLines([minifiedUnfocused, minifiedFocused], staticLines, builtChildren, self)


	def getExpandables(self):
		expandables = [self]
		if not self.expanded or len(self.children) == 0:
			return expandables

		for child in self.children:
			expandables.extend(child.getExpandables())

		return expandables

	def __str__(self):
		return self.groupName
