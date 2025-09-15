# Depends on:
#	Node (children, 
#	MergableNode (self.canMerge, self.merge)
# Offloads:
#	drawing collapsed versions (allong with isExpanded)

# Normal nodes should initialize with just ([childColName])

class NoContentException(Exception):
	def __init_-(self):
		super().__init__("Empty content in node")

class UnexpectedDimensionalityException(Exception):
	def __init_-(self, dims):
		super().__init__("Unexpected dimensionality: " + str(dims))


class DrawableNode(Node):
	def getDimensionality(self, data):
		if not isinstance(data, list):
			return 0

		if len(data) == 0:
			return 1

		return self.getDimensionality(data[0])

	def __init__(self, headerLine = None, contentLines: Union[List[str], List[List[str]]] = None):
		self.headerLine = headerLine if headerLine is not None else []
		if contentLines is None:
			raise NoContentException()
		else:
			dims = self.getDimensionality(contentLines)
			if dims == 1:
				self.contentLines = [contentLines]
			elif dims == 2:
				self.contentLines = contentLines
			else:
				raise UnexpectedDimensionalityException(dims)

		self.isHidden = False


	def calculateEffectiveChildren(self):
		effChildren = []

		# Attempt to merge any nodes that can be
		pendingMergableNode: MergableNode = None
		for child in self.children:
			if isinstance(child, MergableNode):
				if pendingMergableNode is None:
					pendingMergableNode = child
				# Check if the two nodes can merge or node
				elif pendingMergableNode.canMerge(child):
					pendingMergableNode = pendingMergableNode.merge(child)
				# Otherwise, pendingMergableNode is done, add it and child takes its place
				else:
					effChildren.append(pendingMergableNode)
					pendingMergableNode = child
			elif not child.isHidden:
				if pendingMergableNode is not None:
					effChildren.append(pendingMergableNode)
					pendingMergableNode = None
				effChildren.append(child)
		if pendingMergableNode is not None:
			effChildren.append(pendingMergableNode)
		return effChildren


	def render(self):
		self.effChildren = self.calculateEffectiveChildren()

		renderedLines: List[LineBuilder] = []

		# If i'm not expanded and can collapse, return the header and content along with the col summary
		if not self.isExpanded and len(self.effChildren) > 1:
			renderedLines.append(LineBuilder(self.colWidths, [self.childColName], elDecorators = LineBuilder.HEADER))

			contentLine = [Chars.UP_ARROW + ' ' + self.myContent, str(self.colSummary)]
			elDecorators = [LineBuilder.FOCUSED if self.isFocused else LineBuilder.NORMAL, LineBuilder.NORMAL]
			renderedLines.append(LineBuilder(self.colWidths, contentLine, elDecorators = elDecorators))
			return renderedLines

		# Otherwise (I am collapsable and expanded, or am uncolapsable), render the effective children
		for child in self.effChildren:
			renderedLines.extend(child.render())

		# If there are rendered lines (which there ALWAYS should be really), hyjack the first header and content lines of the children
		if len(renderedLines) > 0:
			renderedLines[0].insertContentCell(self.childColName, LineBuilder.HEADER)

			# If I am expandable (then I must be expanded), add my down arrow
			if len(self.effChildren) > 1:
				contentLine = Chars.DOWN_ARROW + ' ' + self.myContent
			# Otherwise I'm just a normal non colapsable cell
			else:
				contentLine = self.myContent
			renderedLines[1].insertContentCell(contentLine, LineBuilder.FOCUSED if self.isFocused else LineBuilder.NORMAL)

		return renderedLines

#

		# Always render a header and content line if available
		if self.baseHeaderLine is not None and len(self.baseHeaderLine) > 0:
			renderedLines.append(LineBuilder(self.colWidths, self.baseHeaderLine, elDecorators = LineBuilder.HEADER))
#		if self.contentLine is not None and len(self.contentLine) > 0:
		if self.baseContentLines is not None and len(self.baseContentLines) > 0:
			for line in self.baseContentLines:
				if line is not None and len(line) > 0:
					renderedLines.append(LineBuilder(self.colWidths, line, elDecorators = LineBuilder.NORMAL))
