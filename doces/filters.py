"""Sample Python probability functions for evaluation by the C simulation."""

import numpy as np


def _real_array(values, name):
    array = np.asarray(values)
    if array.dtype.kind not in "biuf":
        raise TypeError(f"{name} must contain real numbers")
    return np.array(array, dtype=np.float64, copy=True)


def _validate_differences(values):
    differences = _real_array(values, "differences")
    if differences.ndim != 1 or differences.size < 2:
        raise ValueError("differences must be a one-dimensional array of at least two values")
    if not np.all(np.isfinite(differences)):
        raise ValueError("differences must be finite")
    if differences[0] < 0 or not np.all(differences[1:] > differences[:-1]):
        raise ValueError("differences must be nonnegative and strictly increasing")
    return differences


def _readonly_copy(array):
    # An immutable bytes owner also prevents re-enabling writes through .flags.
    return np.frombuffer(array.tobytes(), dtype=np.float64)


def _validate_interpolation(interpolation):
    if not isinstance(interpolation, str) or interpolation not in ("linear", "previous"):
        raise ValueError("interpolation must be 'linear' or 'previous'")
    return interpolation


class ProbabilityTable:
    """An interpolated probability as a function of absolute difference.

    Parameters
    ----------
    differences : one-dimensional array
        At least two finite, strictly increasing, nonnegative differences.
        Values are unnormalized: the default opinion interval [-1, 1] needs
        coverage of [0, 2]. Simulation checks coverage before running.
    probabilities : one-dimensional array
        Matching real, finite probability values in [0, 1].
    interpolation : {"linear", "previous"}, optional
        Defaults to linear interpolation between samples. With "previous",
        each probability is held until the next difference: at an exact knot,
        that knot's probability applies, including the final endpoint.

    Arrays are copied and exposed read-only. Functions and their captured
    parameters are sampled during construction; Python is not called during
    simulation. Interpolation approximates the supplied function; include each
    step's threshold in the grid to represent it exactly with "previous".
    """

    __slots__ = ("_differences", "_probabilities", "_interpolation")

    def __init__(self, differences, probabilities, *, interpolation="linear"):
        interpolation = _validate_interpolation(interpolation)
        differences = _validate_differences(differences)
        probabilities = _real_array(probabilities, "probabilities")
        if probabilities.ndim != 1 or probabilities.shape != differences.shape:
            raise ValueError("probabilities must be one-dimensional and match differences in length")
        if not np.all(np.isfinite(probabilities)):
            raise ValueError("probabilities must be finite")
        if np.any(probabilities < 0) or np.any(probabilities > 1):
            raise ValueError("probabilities must lie within [0, 1]")
        self._differences = _readonly_copy(differences)
        self._probabilities = _readonly_copy(probabilities)
        self._interpolation = interpolation

    @property
    def differences(self):
        """Read-only sample differences."""
        return self._differences

    @property
    def probabilities(self):
        """Read-only sample probabilities."""
        return self._probabilities

    @property
    def interpolation(self):
        """Interpolation method: "linear" or "previous"."""
        return self._interpolation

    @classmethod
    def from_function(cls, function, grid, *, interpolation="linear"):
        """Call ``function(float(difference))`` once for each point in ``grid``.

        The function must return a real, finite scalar probability in [0, 1].
        Exceptions raised by the function propagate unchanged. Changing a
        captured parameter requires constructing or setting a new table.
        interpolation has the same meaning as in the table constructor.
        """
        interpolation = _validate_interpolation(interpolation)
        if not callable(function):
            raise TypeError("function must be callable")
        differences = _validate_differences(grid)
        probabilities = []
        for difference in differences:
            probability = _real_array(function(float(difference)), "function result")
            if probability.ndim != 0:
                raise ValueError("function must return a scalar probability")
            value = float(probability)
            if not np.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("function must return a finite probability within [0, 1]")
            probabilities.append(value)
        return cls(differences, probabilities, interpolation=interpolation)

    def __call__(self, differences):
        """Interpolate scalar or array differences without extrapolation."""
        values = _real_array(differences, "differences")
        if not np.all(np.isfinite(values)):
            raise ValueError("differences must be finite")
        if np.any(values < self._differences[0]) or np.any(values > self._differences[-1]):
            raise ValueError("differences are outside the table domain")
        if self._interpolation == "previous":
            indices = np.searchsorted(self._differences, values, side="right") - 1
            return self._probabilities[indices]
        return np.interp(values, self._differences, self._probabilities)
