from typing import List

#from .node import Node
from .focusableNode import FocusableNode

class IMergableNode:
	pass

# Offloads to Node:
#	- init
#	- _colWidths
#	- isCollapsed
#	- _childHeaderLine
# Overrides:
#	- colWidths
#	- childHeaderLine
# Adds:
#	- canMerge(other)
#	- merge(others)
#	- isMerged
class MergableNode(FocusableNode):
	@staticmethod
	def promote(node: FocusableNode):
		if not isinstance(node, FocusableNode):
			raise TypeError("MergableNode promotion expected FocusableNode but received " + str(type(node)))
		return MergableNode(node._contentLine, node._headerLine, node._colWidths, node._children, node.parent, node.depth, node.colSummary)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.isMerged = False
		self._effColWidths = self._colWidths


	def canMerge(self, other: IMergableNode) -> bool:
		# Cannot merge a collapsed node with any other
		if self.isCollapsed or other.isCollapsed:
			return False

		return self._childHeaderLine == other._childHeaderLine


	def merge(self, others: List[IMergableNode]):
		# Calculate the standardized col widths (cross-node max of each col width)
		maxColWidths = self._colWidths
		for node in others:
			maxColWidths = [max(maxColWidths[c], node._colWidths[c]) for c in range(len(maxColWidths))]

		# Perpetutate those across all nodes, and set merged nodes to reflect the merger
		self._effColWidths = maxColWidths
		self.isMerged = False
		for node in others:
			node._effColWidths = maxColWidths
			node.isMerged = True


	@property
	def colWidths(self):
		return self._effColWidths

	@property
	def childHeaderLine(self):
		if self.isMerged:
			return []
		return self._childHeaderLine
