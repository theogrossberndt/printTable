from .interfaces import IMergableNode
from .node import Node

# Depends on Node having:
#	- parent: HideableNode
#	- children: List[Node]
#	- isExpanded: bool
# Adds:
#	- childrenChanged
#	- isHidden
#	- isCollapsed
#	- effChildren
class HideableNode(Node):
	def __init__(self, *args, **kwargs):
		super().__init(*args, **kwargs)

		# Set to true to initially calculate effective children
		self.childrenChanged = True
		self.isHidden = False
		self._effChildren = self.children


	def hide(self):
		self.isHidden = True
		self.parent.childrenChanged = True

	def show(self):
		self.isHidden = False
		self.parent.childrenChanged = False


	@property
	def isCollapsed(self):
		# For something to be collapsed it must both be unexpanded AND collapsible
		return len(self._effChildren) > 1 and not self.isExpanded


	@property
	def effChildren(self):
		if not self.childrenChanged:
			return self._effChildren

		self._effChildren = []

		# First filter all hidden children and identify clusters of mergable nodes
		clusters = []
		mergables = []
		for child in self.children:
			# Skip ALL hidden children
			if isinstance(child, HideableNode) and child.isHidden:
				continue

			if isinstance(child, IMergableNode):
				# Reset all merge statuses in the recalculation
				child.isMerged = False

				# If this is a brand new mergable cluster, save it
				# Or, if it can be merged into the current cluster, add it too
				if len(mergables) == 0 or mergables[-1].canMerge(child):
					mergables.append(child)
				# Otherwise this is a new mergable cluster, get rid of the old one and replace it
				else:
					clusters.append(mergables)
					mergables = [child]
			else:
				# An entirely non mergable child ends the previous cluster
				if len(mergables) > 0:
					clusters.append(mergables)
					mergables = []

			# All non hidden children get passed through
			self._effChildren.append(child)

		# Then merge all mergable nodes (removes all but the first's headers, and standardizes col widths)
		for cluster in clusters:
			if len(cluster) > 1:
				cluster[0].merge(cluster[1:])

		return self._effChildren
