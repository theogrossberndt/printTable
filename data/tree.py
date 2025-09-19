from .childCondensingNode import ChildCondensingNode
from ..config import Config
from typing import List
import pandas as pd

class ITree:
	pass

BaseNode = ChildCondensingNode

class Tree:
	def __init__(self, df: pd.DataFrame, config: Config):
		self.root = Tree.buildTree(df, config)
		self.root.isExpanded = True

	def render(self):
		return self.root.render()

	# All nodes created from this are built with no parent defined, they can be filled in with a second pass
	@staticmethod
	def _buildTree(df: pd.DataFrame, config: Config, groupName: str, colWidths: List[int], depth: int):
		# If the df is none, this is a leaf node, which is not responsible for printing child column names and have no children (duh)
		if df is None:
			return BaseNode(str(groupName), [], colWidths, [], None, depth)

		# Otherwise, build children, summarize the column, and store the relevant name
		# Remove any columns from the dataframe that are only na
		# This must be done every time, because grouping reduces rows significantly, leading to new dropped columns
		df = df.dropna(axis=1, how='all')

		# Also remove all hidden columns that are before the first non hidden column
		while len(df.columns) > 0:
			if df.columns[0] in config.hiddenCols:
				df.drop(columns = df.columns[0], inplace = True)
			else:
				break

		childColName = str(config.colNameCleanup(df.columns[0]))
		colSummary = str(config.summarize(df, df.columns[0], long = False))
		colSummaryLong = str(config.summarize(df, df.columns[0], long = True))

		# Count the number of non hidden columns left in the df
		colCount = len(set(df.columns).difference(config.hiddenCols))

		# Group by the common column and iterate over the groups, turning each group into its own node
		# However, if there is only a single column left there is nothing to group, so each row will be a leaf node child of this node
		groups: List[tuple] = []
		if colCount > 1:
			childColWidth: int = len(childColName)
			for gn, group in df.groupby(df.columns[0]):
				# The groupname is the value of the first column, so all children should have this column be the same length
				# Calculate the max group name length to get the column width for this node (plus 2 for the arrows for dropdowns)
				childColWidth = max(len(str(gn))+2, childColWidth)

				# Each group turns into its own node, but they all need the same colWidth which is not calculated yet
				# Delay creation until after all groups have been iterated through
				groups.append((gn, group.drop(columns=df.columns[0])))
		else:
			series: pd.Series = df[df.columns[0]].astype(str)
			childColWidth = max(len(childColName), series.str.len().max())
			for val in series:
				groups.append((val, None))

		myColWidths = [*colWidths, childColWidth]

		children = []
		for gn, subDf in groups:
			children.append(Tree._buildTree(subDf, config, gn, myColWidths, depth+1))

		return BaseNode(str(groupName), childColName, myColWidths, children, None, depth, colSummary, colSummaryLong)


	# Iterate through the tree linking children to parents
	@staticmethod
	def _linkParent(child, parent):
		child.parent = parent
		for grandchild in child._children:
			Tree._linkParent(grandchild, child)


	@staticmethod
	def buildTree(df: pd.DataFrame, config: Config) -> ITree:
		rootNode = Tree._buildTree(df, config, 'root', [], 0)

		for child in rootNode._children:
			Tree._linkParent(child, rootNode)

		return rootNode
