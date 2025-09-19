from .focusableNode import FocusableNode
from .leafNode import LeafNode

# Extends the functionality of a node by adding mergeability and hidability to children
# Functions by overriding the children accessor and caching child merger calculations to prevent excessive manipulation
class ChildCondensingNode(FocusableNode):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._effChildren = []
		self.recalculateChildren = True
		self.isHidden = False

	def hide(self):
		self.isHidden = not self.isHidden
		if self.parent is not None:
			self.parent.recalculateChildren = True

	@property
	def children(self):
		if not self.recalculateChildren:
			return self._effChildren

		# Go through the current effChildren and copy any leaf node state back onto the original child
		for child in self._effChildren:
			if isinstance(child, LeafNode):
				child.saveState()

		self.recalculateChildren = False
		self._effChildren = []

		# Create leaf nodes and clump mergable nodes
		currentClump = []
		for child in self._children:
			if child.isHidden:
				continue

			# If a child is already a leaf node, demote it to a focusable node and promote it back to a child condensing node
#			if isinstance(child, LeafNode):
#				focusable = child.demote()
#				focusable = ChildCondensingNode.promote(focusable)
#				focusable.isHidden = child.isHidden
#				self._children[c] = focusable
#				child = focusable

			# If a child is leafable, do it
			if LeafNode.isLeaf(child):
				leaf = LeafNode.promote(child)
#				self._children[c] = leaf
				self._effChildren.append(leaf)

				# If the current clump is empty or the new leaf can be merged with the clump, add it
				if len(currentClump) == 0 or leaf.canMerge(currentClump[0]):
					currentClump.append(leaf)

				# Otherwise, the previous clump is finished
				# Activate the merge, clear it, and start a new one
				else:
					if len(currentClump) > 1:
						currentClump[0].merge(currentClump[1:])
					currentClump = [leaf]

			else:
				# A non leafable node finishes out the current clump, if one exists
				if len(currentClump) > 1:
					currentClump[0].merge(currentClump[1:])
				currentClump = []
				self._effChildren.append(child)

		# If any current clumps are still remaining, merge them
		if len(currentClump) > 1:
			currentClump[0].merge(currentClump[1:])

		return self._effChildren
