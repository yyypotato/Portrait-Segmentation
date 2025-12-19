from .implementations import UNetModel, FCNModel

class ModelFactory:
    @staticmethod
    def get_model(model_name: str, weights_path: str = None):
        if model_name == "U-Net":
            return UNetModel(weights_path)
        elif model_name == "FCN":
            return FCNModel(weights_path)
        else:
            raise ValueError(f"Unknown model: {model_name}")
