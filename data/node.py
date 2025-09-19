from typing import List, Union
from ..drawing import Line, LineBlock, Chars

class INode:
	pass

# Fundamentally takes care of building the basic tree structure from a dataset recursively
# Exposes the following as properties, which can be *carefully* overridden (as to not cause circular dependencies)
#	- contentLine: A list of strings to be rendered as content, or an empty list to skip rendering this.  By default Node modifies the last element of the content line
#	  to add the drop down arrows if the node is collapsible (as returned via self.isCollapsed and len(self.children)), or just the content line if its not collapsible
#	- childHeaderLine: A list of strings to be rendered as a header, or an empty list to skip rendering this
#	- children: A list of Nodes
#	- isCollapsed: A boolean indicating if the node is both collapsible (len(self.children) > 1) and is collapsed (not self.isExpanded)
#	- contentDecorators: A list of line types matching the length of self.contentLine
class Node:
	def __init__(self, contentLine: Union[List[str], str], childHeaderLine: Union[List[str], str], colWidths: List[int], children: List[INode], parent: INode, depth: int, colSummary: str = None, colSummaryLong: str = None):
		self._contentLine = contentLine if isinstance(contentLine, list) else [contentLine]
		self._childHeaderLine = childHeaderLine if isinstance(childHeaderLine, list) else [childHeaderLine]
		self._colWidths = colWidths
		self._children = children
		self.parent = parent
		self.depth = depth
		self.colSummary = colSummary
		self.colSummaryLong = colSummaryLong if colSummaryLong is not None else colSummary
		self.isExpanded = False

	def click(self):
		self.isExpanded = not self.isExpanded

	@property
	def contentLine(self):
		# A collapsed line get an up arrow added to the last element of the content line, and a col summary
		if self.isCollapsed:
			content = [*self._contentLine]
			content[-1] = Chars.UP_ARROW + ' ' + str(content[-1])
			return [*content, str(self.colSummary)]

		# Otherwise, if I am not collapsable (0 or 1 child) return the basic content line
		if len(self.children) <= 1:
			return self._contentLine

		# The only other option is I'm collapsable but not collapsed, in which case add my down arrow to the last content cell
		content = [*self._contentLine]
		content[-1] = Chars.DOWN_ARROW + ' ' + str(content[-1])
		return content

	# Returns the info that should be shown in the status line when an element of the content line is selected
	@property
	def statusLine(self):
		if self.isCollapsed:
			return [*self._contentLine, str(self.colSummaryLong)]
		return self._contentLine


	@property
	def childHeaderLine(self):
		return self._childHeaderLine

	@property
	def colWidths(self):
		return self._colWidths

	@property
	def children(self):
		return self._children

	@property
	def isCollapsed(self):
		return not self.isExpanded and len(self.children) > 1

	@property
	def contentDecorators(self):
		return [Line.NORMAL for c in range(len(self.contentLine))]


	# A collapsed node just gets the child header line on top and the content line plus the summary on bottom
	def _renderCollapsed(self, header, content, colWidths, renderedLines) -> LineBlock:
#		if len(header) > 0:
#			renderedLines.addLine(Line(colWidths, header, self, elDecorators = Line.HEADER))
		if len(header) > 0:
			renderedLines.addLine(Line(colWidths, ['' for _ in header], self, elDecorators = Line.HEADER))
		if len(content) > 0:
			renderedLines.addLine(Line(colWidths, content, self, elDecorators = self.contentDecorators))
		return renderedLines


	# If there are children, render them and hyjack the first header and content lines of the children
	# It is possible there is not a header line (first child is a one column child)
	def _renderWithChildren(self, header, content, colWidths, renderedLines) -> LineBlock:
		for child in self.children:
			renderedLines.addLine(child.render())

		headerAdded = len(header) == 0
		contentAdded = len(content) == 0
		for line, lineType in renderedLines:
			if lineType == Line.HEADER and not headerAdded:
				for headerCell in header[::-1]:
					line.insertContentCell(headerCell, Line.HEADER)
				headerAdded = True
			elif not lineType == Line.HEADER and not contentAdded:
				content, decorators = content[::-1], self.contentDecorators[::-1]
				for c in range(len(content)):
					line.insertContentCell(content[c], decorators[c], self)
				contentAdded = True

			if headerAdded and contentAdded:
				break


		# If we didn't a header, insert it at the top
		if not headerAdded:
			renderedLines.prependLine(Line(colWidths, header, self, elDecorators = Line.HEADER))

		return renderedLines


	# Otherwise (leaf node) just add the raw header and content
	def _renderLeaf(self, header, content, colWidths, renderedLines) -> LineBlock:
		if len(header) > 0:
			renderedLines.addLine(Line(colWidths, header, self, elDecorators = Line.HEADER))
		if len(content) > 0:
			renderedLines.addLine(Line(colWidths, content, self, elDecorators = self.contentDecorators))

		return renderedLines


	def render(self) -> LineBlock:
		renderedLines: LineBlock = LineBlock(self)

		header = self.childHeaderLine
		content = self.contentLine
		colWidths = self.colWidths

		if self.isCollapsed:
			return self._renderCollapsed(header, content, colWidths, renderedLines)

		if len(self.children) > 0:
			return self._renderWithChildren(header, content, colWidths, renderedLines)

		return self._renderLeaf(header, content, colWidths, renderedLines)


	def __str__(self):
		return str(self._contentLine[0])
