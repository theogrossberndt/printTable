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

		self.isFocused = False
		self.hidden = False

		# Set to true to initially calculate effective children
		self.childrenChanged = True


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
		if len(self.effChildren) > 0 and (self.isExpanded or len(self.effChildren) == 1):
			return self.effChildren[0]
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
			if self.parent is not None:
				self.parent.childChanged = True


	# After building all children, convert leaf-able nodes into leaf nodes
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


	def calculateEffectiveChildren(self):
		# Effective children only change if any children's hidden states have changed
		# If the childrenChanged flag has not been set by the child, skip recalculating (its destructive to LeafNodes focus management via merger)
		if not self.childrenChanged:
			return

		self.childrenChanged = False
		self.effChildren = []

		# leaf nodes must be remerged every render because leafs might be hidden between renders
		pendingLeafNode = None
		for child in self.children:
			if child.hidden:
				continue
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
			else:
				if pendingLeafNode is not None:
					self.effChildren.append(pendingLeafNode)
					pendingLeafNode = None
				self.effChildren.append(child)
		if pendingLeafNode is not None:
			self.effChildren.append(pendingLeafNode)


	def render(self):
		self.calculateEffectiveChildren()

		renderedLines: List[LineBuilder] = [HLine(self)]

		# If i'm not expanded and can collapse, return the header and content along with the col summary
		if not self.isExpanded and len(self.effChildren) > 1:
			renderedLines.append(LineBuilder(self.colWidths, [self.childColName], self, elDecorators = LineBuilder.HEADER))

			contentLine = [Chars.UP_ARROW + ' ' + self.myContent, str(self.colSummary)]
			elDecorators = [LineBuilder.FOCUSED if self.isFocused else LineBuilder.NORMAL, LineBuilder.NORMAL]
			renderedLines.append(LineBuilder(self.colWidths, contentLine, self, elDecorators = elDecorators))
			renderedLines.append(HLine(self))
			return renderedLines


		# Otherwise (I am collapsable and expanded, or am uncolapsable), render the effective children
		for child in self.effChildren:
			renderedLines.extend(child.render())

		# If there are rendered lines (which there ALWAYS should be really), hyjack the first header and content lines of the children
		if len(renderedLines) > 0:
			# Find the first non hline
			c = 0
			while c < len(renderedLines) and isinstance(renderedLines[c], HLine):
				c += 1

			renderedLines[c].insertContentCell(self.childColName, LineBuilder.HEADER)

			# If I am expandable (then I must be expanded), add my down arrow
			if len(self.effChildren) > 1:
				contentLine = Chars.DOWN_ARROW + ' ' + self.myContent
			# Otherwise I'm just a normal non colapsable cell
			else:
				contentLine = self.myContent
			renderedLines[c+1].insertContentCell(contentLine, LineBuilder.FOCUSED if self.isFocused else LineBuilder.NORMAL)

		renderedLines.append(HLine(self))

		return renderedLines


	def getTopColWidths(self):
		if not self.isExpanded and len(self.effChildren) > 1:
			return self.colWidths
		return self.effChildren[0].getTopColWidths()

	def getBottomColWidths(self):
		if not self.isExpanded and len(self.effChildren) > 1:
			return self.colWidths
		return self.effChildren[-1].getBottomColWidths()

	def getTopContentLen(self):
		if not self.isExpanded and len(self.effChildren) > 1:
			return 2
		return self.effChildren[0].getTopContentLen() + 1

	def getBottomContentLen(self):
		if not self.isExpanded and len(self.effChildren) > 1:
			return 2
		return self.effChildren[-1].getBottomContentLen() + 1

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
	def __init__(self, node: Node, baseHeaderLine = None, baseContentLines = None, colWidths = None, parent = None, hidden = None, isFocused = None, depth = None, focusedLineIdx = None, focusedCellIdx = None):
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
			self.focusedLineIdx = 0
			self.focusedCellIdx = 0
		else:
			self.baseHeaderLine = baseHeaderLine
			self.baseContentLines = baseContentLines
			self.colWidths = colWidths
			self.parent = parent
			self.hidden = hidden
			self.isFocused = isFocused
			self.depth = depth
			self.focusedLineIdx = focusedLineIdx
			self.focusedCellIdx = focusedCellIdx

		self.children = []
		self.canCollapse = False
		self.isExpanded = False
		self.isMerged = False


	def merge(self, other):
		baseContentLines = [*self.baseContentLines, *other.baseContentLines]
		colWidths = [max(self.colWidths[c], other.colWidths[c]) for c in range(len(self.colWidths))]

		# TODO: Fix merging focus logic
		isFocused = other.isFocused or self.isFocused
		if not isFocused:
			focusedLineIdx = 0
			focusedCellIdx = 0
		focusedLineIdx = other.focusedLineIdx if other.isFocused else self.focusedLineIdx
		focusedCellIdx = other.focusedCellIdx if other.isFocused else self.focusedCellIdx

		newNode = LeafNode(None, self.baseHeaderLine, baseContentLines, colWidths, self.parent, self.hidden, isFocused, self.depth, focusedLineIdx, focusedCellIdx)
		return newNode

	# Just copy the base header line into the headerLine (so stealing doesnt effect initialization)
	# and do the same for the content line
#	def _rumpelstiltskin(self):
#		self.headerLine = [*self.baseHeaderLine]
#
#		self.contentLine = self.baseContentLines[0]
#		if len(self.baseContentLines) > 1:
#			self.additionalContentLines: List[List[str]] = self.baseContentLines[1:]
#		else:
#			self.additionalContentLines = []
#
#		self.topColWidths = [*self.colWidths]
#		self.bottomColWidths = [*self.colWidths]
#
#		self.topContentLen = len(self.contentLine)
#		self.bottomContentLen = len(self.contentLine)
#
#		return

	def render(self):
		self.effChildren = []
		renderedLines: List[LineBuilder] = [HLine(self)]

		if self.baseHeaderLine is not None and len(self.baseHeaderLine) > 0:
			renderedLines.append(LineBuilder(self.colWidths, self.baseHeaderLine, self, elDecorators = LineBuilder.HEADER))
		if self.baseContentLines is not None and len(self.baseContentLines) > 0:
			for r in range(len(self.baseContentLines)):
				line = self.baseContentLines[r]
				if line is None or len(line) == 0:
					continue

				if r == self.focusedLineIdx and self.isFocused:
					elDecorators = [LineBuilder.FOCUSED if c == self.focusedCellIdx else LineBuilder.NORMAL for c in range(len(line))]
				else:
					elDecorators = LineBuilder.NORMAL
				renderedLines.append(LineBuilder(self.colWidths, line, self, elDecorators = elDecorators))

		# Only prepend an hline before the child starts if the first line was not absorbed
		# Otherwise there will be a line between the first and second lines weirdly
		renderedLines.append(HLine(self))
		return renderedLines

	def __str__(self):
		return str(self.baseContentLines[self.focusedLineIdx][self.focusedCellIdx]) + ' ' + str(self.focusedLineIdx) + ', ' + str(self.focusedCellIdx)

	def focusDown(self):
		# If we can focus down within the content lines, do so
		if self.focusedLineIdx+1 < len(self.baseContentLines):
			self.focusedLineIdx += 1
			return self
		# Otherwise, do the default node focus down (pick next child)
		return super().focusDown()

	def focusUp(self):
		# If we can focus up within the content lines, do it
		if self.focusedLineIdx-1 >= 0:
			self.focusedLineIdx -= 1
			return self
		# Otherwise ivoke the default focus up
		return super().focusUp()


	def focusLeft(self):
		if self.focusedCellIdx-1 < 0:
			return self.parent
		self.focusedCellIdx -= 1
		return self

	def focusRight(self):
		if self.focusedCellIdx+1 < len(self.baseContentLines[self.focusedLineIdx]):
			self.focusedCellIdx += 1
		return self


	def getTopColWidths(self):
		return self.colWidths

	def getBottomColWidths(self):
		return self.colWidths

	def getTopContentLen(self):
		return len(self.baseContentLines[0])

	def getBottomContentLen(self):
		return len(self.baseContentLines[-1])
