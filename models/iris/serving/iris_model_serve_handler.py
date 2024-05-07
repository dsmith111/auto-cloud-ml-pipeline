import torch
from ts.torch_handler.base_handler import BaseHandler
# index_to_name.json' is missing. Inference output will not include class name.
class IrisHandler(BaseHandler):
    petal_label_mapping: dict = {
        0: 'setosa',
        1: 'versicolor',
        2: 'virginica'
    }

    def __init__(self):
        super().__init__()

    def preprocess(self, data):
        # Extract features from the input data. It'll either come in as a list of raw json bodies
        # or as the data within instances
        print(data)
        features = None
        if 'body' in data[0] and type(data[0]) == dict: # TorchServe
            instances = data[0].get('body') or data[0].get('data')
            features = instances.get('instances')
        else: # KFServing
            features = data

        # Convert features to tensor
        features_tensor = torch.tensor(features, dtype=torch.float32)
        return features_tensor

    def inference(self, features_tensor):
        # Make predictions
        with torch.no_grad():
            outputs = self.model(features_tensor)
        return outputs

    def postprocess(self, outputs):
        # Convert predictions to class labels
        _, predicted = torch.max(outputs, 1)
        predicted = [self.petal_label_mapping[p] for p in predicted.numpy().tolist()]
        return predicted

_service = IrisHandler()
