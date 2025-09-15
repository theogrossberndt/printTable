from .hline import HLine
from .lineBuilder import LineBuilder
from typing import List

from .node import Node

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
		self.effChildren = []
		renderedLines: List[LineBuilder] = []
#		renderedLines: List[LineBuilder] = [HLine(self)]

		# Always render a header and content line if available
		if self.baseHeaderLine is not None and len(self.baseHeaderLine) > 0:
			renderedLines.append(LineBuilder(self.colWidths, self.baseHeaderLine, elDecorators = LineBuilder.HEADER))
#		if self.contentLine is not None and len(self.contentLine) > 0:
		if self.baseContentLines is not None and len(self.baseContentLines) > 0:
			for line in self.baseContentLines:
				if line is not None and len(line) > 0:
					renderedLines.append(LineBuilder(self.colWidths, line, elDecorators = LineBuilder.NORMAL))

		# This will only be the case if this node was NOT rumpelstilskin'd
#		if len(renderedLines) > 0:
#			renderedLines.insert(0, HLine(self))

#		for contentLine in self.additionalContentLines:
#			if contentLine is not None and len(contentLine) > 0:
#				renderedLines.append(LineBuilder(self.topColWidths, contentLine, elDecorators = LineBuilder.NORMAL))

		# Only prepend an hline before the child starts if the first line was not absorbed
		# Otherwise there will be a line between the first and second lines weirdly
#		renderedLines.append(HLine(self))
		return renderedLines

	def __str__(self):
		return self.baseContentLines[0][0]

