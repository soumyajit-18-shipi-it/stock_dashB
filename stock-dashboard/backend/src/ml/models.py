from abc import ABC, abstractmethod
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

class BaseModel(ABC):
    @abstractmethod
    def train_and_predict(self, X_train, y_train, X_predict) -> float:
        pass

class LinearRegressionModel(BaseModel):
    def train_and_predict(self, X_train, y_train, X_predict) -> float:
        model = LinearRegression()
        model.fit(X_train, y_train)
        prediction = model.predict(X_predict)
        return float(prediction[0])

class RandomForestModel(BaseModel):
    def train_and_predict(self, X_train, y_train, X_predict) -> float:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        prediction = model.predict(X_predict)
        return float(prediction[0])
