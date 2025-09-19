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


	@property
	def children(self):
		if not self.recalculateChildren:
			return self._effChildren

		self.recalculateChildren = False
		self._effChildren = []

		# Create leaf nodes and clump mergable nodes
		currentClump = []
		for child in self._children:
			if child.isHidden:
				continue

			# If a child is leafable, do it
			if LeafNode.isLeaf(child):
				leaf = LeafNode.promote(child)
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
