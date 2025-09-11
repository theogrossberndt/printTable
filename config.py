import pandas as pd
from typing import Set

class Config:
	def __init__(self, df: pd.DataFrame, countableCols: Set[str], hiddenCols: Set[str]):
		self.df = df
		self.countableCols = countableCols
		self.hiddenCols = hiddenCols


	def summarize(self, df: pd.DataFrame, colName: str):
		summary = 0
		for col in df.columns:
			if col in self.countableCols:
				summary += pd.to_numeric(df[col].fillna(0), downcast='integer').sum()
		return 'Total: ' + str(summary)


	def colNameCleanup(self, v):
		if isinstance(v, str):
			subIdx = v.find('_')
			if subIdx > 0:
				return v[subIdx+1:]
			return v

		return [self.colNameCleanup(val) for val in v]
