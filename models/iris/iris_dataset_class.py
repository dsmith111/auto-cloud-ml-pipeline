import torch
import pandas as pd

class IrisDataset(torch.utils.data.Dataset):

    def __init__(self, data: pd.DataFrame, target_column: str):
        super().__init__()
        self.data = data
        self.target_column = target_column

    def __len__(self):
        if self.data is None:
            return 0
        return self.data.shape[0]

    def __getitem__(self, idx):
        features = self.data.loc[idx, self.data.columns != self.target_column]
        target = self.data.loc[idx, self.data.columns == self.target_column]

        features = torch.tensor(features.values, dtype=torch.float32)
        target = torch.tensor(target.values[0], dtype=torch.long)
        return features, target