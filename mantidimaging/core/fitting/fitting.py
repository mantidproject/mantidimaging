# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from abc import abstractmethod, ABC

from math import sqrt
import numpy as np
from scipy.special import erf
from scipy.optimize import minimize


class BaseFittingFunction(ABC):
    parameter_names: list[str]

    def get_parameter_names(self) -> list[str]:
        return list(self.parameter_names)

    @abstractmethod
    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        ...


class ErfStepFunction(BaseFittingFunction):
    parameter_names = ["mu", "sigma", "h", "a"]

    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        mu, sigma, h, a = params
        y = h * 0.5 * (1 + erf((xdata - mu) / (sigma * sqrt(2)))) + a
        return y


class FittingEngine:

    def __init__(self, model: BaseFittingFunction):
        self.model = model

    def find_best_fit(self, xdata: np.ndarray, ydata: np.ndarray, initial_params: list[float], max_iter: int):
        f = lambda params: ((model.evaluate(xdata, params) - ydata)**2).sum()

        result = minimize(f, initial_params, method="Nelder-Mead", options={"maxiter": max_iter})
        print(result)
        return result


if __name__ == '__main__':
    from matplotlib import pyplot
    from scipy.stats import norm
    rng = np.random.default_rng()

    x = np.linspace(0, 10, 200)
    y = norm.cdf(x, loc=5, scale=0.8) + rng.standard_normal(x.shape) * 0.1 + 3

    pyplot.plot(x, y, label="data")
    pyplot.grid()

    model = ErfStepFunction()
    fitter = FittingEngine(model)
    init_params = [5, 1, 1, 1]

    y_fitted = model.evaluate(x, init_params)
    pyplot.plot(x, y_fitted, label="init")

    for i in range(1, 20, 1):
        fit_result = fitter.find_best_fit(x, y, init_params, i)
        y_fitted = model.evaluate(x, fit_result.x)
        pyplot.plot(x, y_fitted, color="gray")

    fit_result = fitter.find_best_fit(x, y, init_params, 1000)

    y_fitted = model.evaluate(x, fit_result.x)
    pyplot.plot(x, y_fitted, label="fitted")

    pyplot.legend(loc="best")
    pyplot.show()
