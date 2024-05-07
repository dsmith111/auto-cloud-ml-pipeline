import torch

class Classifier(torch.nn.Module):
    
    def __init__(self, input_size, output_size):
        super().__init__()
        self.fc1 = torch.nn.Linear(input_size, input_size * 2)
        self.fc2 = torch.nn.Linear(input_size * 2, input_size * 2)
        self.fc3 = torch.nn.Linear(input_size * 2, input_size)
        self.fc4 = torch.nn.Linear(input_size, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        x = self.fc4(x)
        return x