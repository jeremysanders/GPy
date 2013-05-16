import numpy as np
from likelihood import likelihood

class Gaussian(likelihood):
    """
    Likelihood class for doing Expectation propagation

    :param Y: observed output (Nx1 numpy.darray)
    ..Note:: Y values allowed depend on the likelihood_function used
    :param variance : 
    :param normalize:  whether to normalize the data before computing (predictions will be in original scales)
    :type normalize: False|True
    """
    def __init__(self, data, variance=1., normalize=False):
        self.is_heteroscedastic = False
        self.Nparams = 1
        self.Z = 0. # a correction factor which accounts for the approximation made
        N, self.D = data.shape

        # normalization
        if normalize:
            self._bias = data.mean(0)[None, :]
            self._scale = data.std(0)[None, :]
            # Don't scale outputs which have zero variance to zero.
            self._scale[np.nonzero(self._scale == 0.)] = 1.0e-3
        else:
            self._bias = np.zeros((1, self.D))
            self._scale = np.ones((1, self.D))

        self.set_data(data)

        self._variance = np.asarray(variance) + 1.
        self._set_params(np.asarray(variance))

    def set_data(self, data):
        self.data = data
        self.N, D = data.shape
        assert D == self.D
        self.Y = (self.data - self._bias) / self._scale
        if D > self.N:
            self.YYT = np.dot(self.Y, self.Y.T)
            self.trYYT = np.trace(self.YYT)
        else:
            self.YYT = None
            self.trYYT = np.sum(np.square(self.Y))

    def _get_params(self):
        return np.asarray(self._variance)

    def _get_param_names(self):
        return ["noise_variance"]

    def _set_params(self, x):
        if self._variance != x:
            self.precision = 1. / x
            self.covariance_matrix = np.eye(self.N) * x
            self.V = (self.precision) * self.Y
            self._variance = x

    def predictive_values(self, mu, var, full_cov):
        """
        Un-normalize the prediction and add the likelihood variance, then return the 5%, 95% interval
        """
        mean = mu * self._scale + self._bias
        if full_cov:
            if self.D > 1:
                raise NotImplementedError, "TODO"
                # Note. for D>1, we need to re-normalise all the outputs independently.
                # This will mess up computations of diag(true_var), below.
                # note that the upper, lower quantiles should be the same shape as mean
            true_var = (var + np.eye(var.shape[0]) * self._variance) * self._scale ** 2
            _5pc = mean - 2.*np.sqrt(np.diag(true_var))
            _95pc = mean + 2.*np.sqrt(np.diag(true_var))
        else:
            true_var = (var + self._variance) * self._scale ** 2
            _5pc = mean - 2.*np.sqrt(true_var)
            _95pc = mean + 2.*np.sqrt(true_var)
        return mean, true_var, _5pc, _95pc

    def fit_full(self):
        """
        No approximations needed
        """
        pass

    def _gradients(self, partial):
        return np.sum(partial)
