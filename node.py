import pandas as pd
from .hline import HLine
from .lineBuilder import LineBuilder
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

		self.focusedChildIdx = 0
		self.isFocused = False
		self.hidden = False


	# Focus down always focuses on the parent's next child
	# If the parent has no remaining children, focus down on the parent
	# Parent will NOT be None (root is always there - and RootNode overrides this for end-of-table behavior)
	def focusDown(self):
		myChildIdx = self.parent.effChildren.index(self)
		if myChildIdx == len(self.parent.effChildren)-1:
			return self.parent.focusDown()
		return self.parent.effChildren[myChildIdx+1]

	# Same concept as focus up, but in reverse
	def focusUp(self):
		myChildIdx = self.parent.effChildren.index(self)
		if myChildIdx == 0:
			return self.parent.focusUp()
		return self.parent.effChildren[myChildIdx-1]

	# Focus on the parent as long as the root node would not be focused
	def focusLeft(self):
		if self.parent.parent is not None:
			return self.parent
		return self

	# Shift focus to a certain child
	# If we have shifted left out of here before, remember the index
	def focusRight(self):
		if len(self.children) > 0:
			return self.children[0]
		return self

	def focusOut(self):
		self.isFocused = False

	def focusIn(self):
		self.isFocused = True


	# Focus happens on a first line, which means that if this node is focused, it might be this node or any
	# of the nodes it rumpelstiltskin'd recursively
	# Consequentially, a node needs to handle focus left/right, and click
	def handleKey(self, keyCode):
		if keyCode == Node.CLICK and self.canCollapse:
			self.isExpanded = not self.isExpanded

		if keyCode == Node.HIDE:
			self.hidden = True


	# After building all children, convert leaf-able nodes into LeafNodes
	# This needs to be done after everything is built because we want leaf nodes to be as shallow
	# as possible to avoid merging, so this is not called from the constructor
	def _leafifyChildren(self):
		for c in range(len(self.children)):
			if LeafNode.isLeaf(self.children[c]):
				leafChild = LeafNode(self.children[c])
				self.children[c] = leafChild
			else:
				self.children[c]._leafifyChildren()


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
		self.effChildren = []

		# leaf nodes must be remerged every render because leafs might be hidden between renders
		pendingLeafNode = None
		for child in self.children:
			if isinstance(child, LeafNode):
				if pendingLeafNode is None:
					pendingLeafNode = child
				# Leaf nodes can only be merged if their headers match
				elif pendingLeafNode.baseHeaderLine == child.baseHeaderLine:
					pendingLeafNode = pendingLeafNode.merge(child)
				# Otherwise, pendingLeafNode is done, add it and child takes its place
				else:
					self.effChildren.append(pendingLeafNode)
					pendingLeafNode = child
#				self.effChildren.append(child)
			elif not child.hidden:
				if pendingLeafNode is not None:
					self.effChildren.append(pendingLeafNode)
					pendingLeafNode = None
				self.effChildren.append(child)
		if pendingLeafNode is not None:
			self.effChildren.append(pendingLeafNode)

		# Leaf nodes are a special case, as they have nothing to steal and no expansion possibility
		if len(self.effChildren) == 0:
			self.headerLine = []
			self.contentLine = [self.myContent]

			self.topColWidths = self.colWidths
			self.bottomColWidths = self.colWidths

			self.topContentLen = 1
			self.bottomContentLen = 1
			return True

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
			return False


		# Otherwise, allow each child to reslove its own stealable content
		for child in self.effChildren:
			child.rumpelstiltskin()

		# After resolving all children, promote headers upwards when possible
		# TODO: This leads to an issue of non collapsable siblings having different sized columns
		# Resolution would be to redefine what a leaf node is as any non expandable node :(
#		for c in range(len(nonHiddenChildren)-1, 0, -1):
#			bottomChild = nonHiddenChildren[c]
#			topChild = nonHiddenChildren[c-1]
#			# If headers match, delete the bottom child's headerLine and sync col widths (based on topColWidths)
#			if isinstance(topChild, LeafNode) and isinstance(bottomChild, LeafNode) and topChild.headerLine == bottomChild.headerLine:
#				for c in range(len(topChild.topColWidths)):
#					colWidth = max(topChild.topColWidths[c], bottomChild.topColWidths[c])
#				bottomChild.headerLine = []

		# Generate my own header and content lines
		self.headerLine = [self.childColName] if self.childColName is not None else []
		self.contentLine = [Chars.UP_ARROW + ' ' + self.myContent] if self.canCollapse else [self.myContent]

		# And perform the thievery
		firstChild = self.effChildren[0]
		lastChild = self.effChildren[-1]

		self.headerLine.extend(firstChild.headerLine)
		firstChild.headerLine = []

		self.contentLine.extend(firstChild.contentLine)
		firstChild.contentLine = []

		self.topColWidths = firstChild.topColWidths
		self.bottomColWidths = lastChild.bottomColWidths

		self.topContentLen = firstChild.topContentLen+1
		self.bottomContentLen = lastChild.bottomContentLen+1
		return False


	def render(self):
		renderedLines: List[LineBuilder] = []

		# Always render a header and content line if available
		if self.headerLine is not None and len(self.headerLine) > 0:
			renderedLines.append(LineBuilder(self.topColWidths, self.headerLine, elDecorators = LineBuilder.HEADER))
		if self.contentLine is not None and len(self.contentLine) > 0:
			renderedLines.append(LineBuilder(self.topColWidths, self.contentLine, elDecorators = LineBuilder.NORMAL))

		# Only prepend an hline before the child starts if the first line was not absorbed
		# Otherwise there will be a line between the first and second lines weirdly
		if len(renderedLines) > 0:
			renderedLines.insert(0, HLine(self))

		# If I have children and am expanded, or am uncolapsable, render the children
		if not self.canCollapse or self.isExpanded:
			for child in self.effChildren:
				renderedLines.extend(child.render())

		renderedLines.append(HLine(self))
		return renderedLines


	def __str__(self):
		return self.myContent


# A leaf node is a node that cannot be collapsed, with no children that can be collapsed
class LeafNode(Node):
	@staticmethod
	def isLeaf(node: Node) -> bool:
		firstChild = None
		for child in node.children:
			if child.hidden:
				continue
			# More than one child is a collapsible node
			if firstChild is not None:
				return False
			firstChild = child
		# No children is definitely a leaf
		if firstChild is None:
			return True
		# Otherwise, traverse down to make sure all desendants are also leaves
		return LeafNode.isLeaf(firstChild)


	# Receives a node that will be converted into a leaf node via condensing children
	# A leaf node is a single line of data with potentially multiple columns
	# To stay rumpelstiltskin-able, it needs to expose:
	#	topContentLen, bottomContentLen
	#	topColWidths, bottomColWidths
	#	contentLine, headerLine
	def __init__(self, node: Node, baseHeaderLine = None, baseContentLines = None, colWidths = None, parent = None, hidden = None, isFocused = None, depth = None):
		if node is not None:
			self.baseHeaderLine = []
			self.baseContentLines: List[List[str]] = [[]]

			deepestChild = node
			while len(deepestChild.children) > 0:
				self.baseHeaderLine.append(deepestChild.childColName)
				self.baseContentLines[0].append(deepestChild.myContent)
				deepestChild = deepestChild.children[0]

			self.baseContentLines[0].append(deepestChild.myContent)

			self.colWidths = deepestChild.colWidths

			self.parent = node.parent
			self.hidden = node.hidden

			self.isFocused = node.isFocused

			self.depth = node.depth
		else:
			self.baseHeaderLine = baseHeaderLine
			self.baseContentLines = baseContentLines
			self.colWidths = colWidths
			self.parent = parent
			self.hidden = hidden
			self.isFocused = isFocused
			self.depth = depth

		self.children = []
		self.canCollapse = False
		self.isExpanded = False
		self.isMerged = False


	def merge(self, other):
		baseContentLines = [*self.baseContentLines, *other.baseContentLines]
		colWidths = [max(self.colWidths[c], other.colWidths[c]) for c in range(len(self.colWidths))]

		newNode = LeafNode(None, self.baseHeaderLine, baseContentLines, colWidths, self.parent, self.hidden, self.isFocused, self.depth)
		return newNode

	# Just copy the base header line into the headerLine (so stealing doesnt effect initialization)
	# and do the same for the content line
	def rumpelstiltskin(self):
		self.headerLine = [*self.baseHeaderLine]

		self.contentLine = self.baseContentLines[0]
		if len(self.baseContentLines) > 1:
			self.additionalContentLines: List[List[str]] = self.baseContentLines[1:]
		else:
			self.additionalContentLines = []

		self.topColWidths = [*self.colWidths]
		self.bottomColWidths = [*self.colWidths]

		self.topContentLen = len(self.contentLine)
		self.bottomContentLen = len(self.contentLine)

		return

	def render(self):
		renderedLines: List[LineBuilder] = []

		# Always render a header and content line if available
		if self.headerLine is not None and len(self.headerLine) > 0:
			renderedLines.append(LineBuilder(self.topColWidths, self.headerLine, elDecorators = LineBuilder.HEADER))
		if self.contentLine is not None and len(self.contentLine) > 0:
			renderedLines.append(LineBuilder(self.topColWidths, self.contentLine, elDecorators = LineBuilder.NORMAL))

		# This will only be the case if this node was NOT rumpelstilskin'd
		if len(renderedLines) > 0:
			renderedLines.insert(0, HLine(self))

		for contentLine in self.additionalContentLines:
			if contentLine is not None and len(contentLine) > 0:
				renderedLines.append(LineBuilder(self.topColWidths, contentLine, elDecorators = LineBuilder.NORMAL))

		# Only prepend an hline before the child starts if the first line was not absorbed
		# Otherwise there will be a line between the first and second lines weirdly
		renderedLines.append(HLine(self))
		return renderedLines

	def __str__(self):
		return self.baseContentLines[0][0]
