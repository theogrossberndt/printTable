import pandas as pd
from .hline import HLine
from .line import Line
from .chars import Chars
from typing import List
import curses
from .config import Config

# Fundamentally a Node owns two things:
#	- The group name, which is the value of the parent's first column that all elements this node received as children share in common.
#	  This is the content of the Node, when someone selects this node this is what they identify it by
#	- The name of the first column of children.
class Node:
	FOCUS_LEFT = 0
	FOCUS_RIGHT = 1
	CLICK = 2
	HIDE = 3

	def __init__(self, config: Config, groupName: str, colWidths: List[int], depth: int, parent):
		self.config = config

		self.myContent: str = str(groupName)

		# colWidths is an accumulated list of all the column widths of the parents, with the last element being the width
		# of the __first column__ the current node is responsible for printing (group name)
		self.colWidths: List[int] = [*colWidths]

		self.depth = depth
		self.parent = parent

		# If the df is none, this is a leaf node, which is not responsible for printing child column names and have no children (duh)
		if config.df is None:
			self.childColName = None
			self.children: List[Node] = []

		# Otherwise, build children, summarize the column, and store the relevant name
		else:
			# Remove any columns from the dataframe that are only na
			# This must be done every time, because grouping reduces rows significantly, leading to new dropped columns
			df: pd.DataFrame = config.df.dropna(axis=1, how='all')

			# Also remove all hidden columns that are before the first non hidden column
			while len(df.columns) > 0:
				if df.columns[0] in config.hiddenCols:
					df.drop(columns = df.columns[0], inplace = True)
				else:
					break

			self.childColName: str = Chars.colNameCleanup(df.columns[0])
			self.colSummary = config.summarize(df, df.columns[0])

			self._buildChildren(df)

		self.canCollapse = len(self.children) > 1
		self.isExpanded = False

		self.focusedNode = self
		self.focusedIdx = 0
		self.isFocused = False
		self.hidden = False


	# Focus happens on a first line, which means that if this node is focused, it might be this node or any
	# of the nodes it rumpelstiltskin'd recursively
	# Consequentially, a node needs to handle focus left/right, and click
	def handleKey(self, keyCode):
		# If the node is not expanded and can collapse, focus left/right can be ignored as only the first column (me) can be focused
		if not self.isExpanded and self.canCollapse:
			self.focusedNode = self
			self.focusedIdx = 0
			if keyCode == Node.FOCUS_LEFT or keyCode == Node.FOCUS_RIGHT:
				return

		# Otherwise, left/right means focusing on the parent/child of the focused node
		if keyCode == Node.FOCUS_LEFT:
			# DONT LET ROOT BECOME FOCUSED
			if self.focusedNode.parent is not None and self.focusedNode.parent.depth > 1:
				self.focusedNode = self.focusedNode.parent
				self.focusedIdx -= 1
		if keyCode == Node.FOCUS_RIGHT:
			if len(self.focusedNode.children) > 0:
				self.focusedNode = self.focusedNode.children[0]
				self.focusedIdx += 1

		# If we have clicked and the focusedNode can collapse, flip its expansion
		if keyCode == Node.CLICK and self.focusedNode.canCollapse:
			self.focusedNode.isExpanded = not self.focusedNode.isExpanded

		if keyCode == Node.HIDE:
			self.focusedNode.hidden = True


	def _buildChildren(self, df: pd.DataFrame):
		# The column name also needs to fit in the column, so add that
		childColWidth: int = len(self.childColName)

		# Count the number of non hidden columns left in the df
		colCount = len(set(df.columns).difference(self.config.hiddenCols))

		# Group by the common column and iterate over the groups
		# However, if there is only a single column left there is nothing to group
		# Iterate over the series adding each element as its own leaf node (a Node with a None dataframe)
		groups: List(tuple) = []
		if colCount > 1:
			for groupName, group in df.groupby(df.columns[0]):
				# The groupname is the value of the first column, so all children should have this column be the same length
				# Calculate the max group name length to get the column width for this node
				# Also add 2 to each length to account for drop down arrows
				# TODO: add definable tostr support perhaps
				childColWidth = max(len(str(groupName))+2, childColWidth)

				# Each group turns into its own node, but they all need the same colWidth which is not calculated yet
				# Delay creation until after all groups have been iterated through
				groups.append((groupName, group.drop(columns=df.columns[0])))
		else:
			series: pd.Series = df[df.columns[0]].astype(str)
			childColWidth = max(childColWidth, series.str.len().max())
			for val in series:
				groups.append((val, None))

		self.colWidths.append(childColWidth)
		self.children = []
		for groupName, group in groups:
			config = Config(group, self.config.countableCols, self.config.hiddenCols)
			self.children.append(Node(config, groupName, self.colWidths, self.depth+1, self))


	# Allow each node to select the current content for its header and content lines (based on expansion state)
	# Also resolve the current top and bottom col widths for each node
	# Then, absorb the header and content lines from the first child, and the top/bottom col widths from the relevant children
	def rumpelstiltskin(self):
		nonHiddenChildren = [child for child in self.children if not child.hidden]
		# Leaf nodes are a special case, as they have nothing to steal and no expansion possibility
		if len(nonHiddenChildren) == 0:
			self.headerLine = []
			self.contentLine = [self.myContent]

			self.topColWidths = self.colWidths
			self.bottomColWidths = self.colWidths

			self.topContentLen = 1
			self.bottomContentLen = 1
			return

		# If this is an unexpanded node and it is colapsible (more than 1 child), then it terminates here
		if not self.isExpanded and self.canCollapse:
			# An unexpanded line has its own content as the first cell, then the table summary as its second cell
			self.contentLine = [Chars.DOWN_ARROW + ' ' + self.myContent, str(self.colSummary)]

			# An unexpanded line also has no header line to print
			self.headerLine = ['']

			# Col widths already has the child col appended to it, so no modification is needed
			self.topColWidths = self.colWidths
			self.bottomColWidths = self.colWidths

			self.topContentLen = 2
			self.bottomContentLen = 2
			return


		# Otherwise, allow each child to reslove its own stealable content
		for child in nonHiddenChildren:
			child.rumpelstiltskin()

		# After resolving all children, promote headers upwards when possible
		# TODO: This leads to an issue of non collapsable siblings having different sized columns
		# Resolution would be to redefine what a leaf node is as any non expandable node :(
#		for c in range(len(nonHiddenChildren)-1, 0, -1):
#			bottomChild = nonHiddenChildren[c]
#			topChild = nonHiddenChildren[c-1]
#			if bottomChild.headerLine == topChild.headerLine:
#				bottomChild.headerLine = []

		# Generate my own header and content lines
		self.headerLine = [self.childColName] if self.childColName is not None else []
		self.contentLine = [Chars.UP_ARROW + ' ' + self.myContent] if self.canCollapse else [self.myContent]

		# And perform the thievery
		firstChild = nonHiddenChildren[0]
		lastChild = nonHiddenChildren[-1]

		self.headerLine.extend(firstChild.headerLine)
		firstChild.headerLine = []
		self.contentLine.extend(firstChild.contentLine)
		firstChild.contentLine = []

		self.topColWidths = firstChild.topColWidths
		self.bottomColWidths = lastChild.bottomColWidths

		self.topContentLen = firstChild.topContentLen+1
		self.bottomContentLen = lastChild.bottomContentLen+1


	def render(self):
		renderedLines: List[Line] = []

		# Always render a header and content line if available
		if self.headerLine is not None and len(self.headerLine) > 0:
			renderedLines.append(Line(self.headerLine, self, lineType = Line.HEADER, colWidths = self.topColWidths))
		if self.contentLine is not None and len(self.contentLine) > 0:
			renderedLines.append(Line(self.contentLine, self, colWidths = self.topColWidths))

		# Only prepend an hline before the child starts if the first line was not absorbed
		# Otherwise there will be a line between the first and second lines weirdly
		if len(renderedLines) > 0:
			renderedLines.insert(0, HLine(self))

		# If I have children and am expanded, or am uncolapsable, render the children
		if not self.canCollapse or self.isExpanded:
			for child in self.children:
				if not child.hidden:
					renderedLines.extend(child.render())

		renderedLines.append(HLine(self))
		return renderedLines


	def __str__(self):
		return self.myContent
