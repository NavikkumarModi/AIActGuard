"""Predictable-mixture empirical-Bernstein anytime-valid confidence
sequences — the specific statistical method `priority.py` needs to
compute an upper confidence bound on a bin's true violation rate from a
stream of audit findings that keeps arriving indefinitely (not a fixed
sample), without the bound needing periodic recomputation to stay valid.

Ported from the `confseq` package (MIT license) by Steve Howard, with
contributors Ian Waudby-Smith and Aaditya Ramdas —
https://github.com/gostevehoward/confseq — which arrived as a reference
implementation via the user's own research on adaptively-routed agent
systems. Only this one code path is ported, not the full library: the
published `confseq` package on PyPI requires a compiled CMake build that
failed on this machine and can't be relied on to install cleanly for
everyone, while this path is pure NumPy — the rest of the library
(plotting, other betting strategies, without-replacement sampling) isn't
used here and pulls in scipy/matplotlib/multiprocess for no benefit to
this module. See the original repository for the full method and paper
references (Waudby-Smith & Ramdas, "Estimating means of bounded random
variables by betting").
"""

from __future__ import annotations

import math
from typing import Callable, Optional

import numpy as np

RealArray = np.ndarray


def _lambda_predmix_eb(
    x: RealArray,
    truncation: float = math.inf,
    alpha: float = 0.05,
    fixed_n: Optional[int] = None,
    prior_mean: float = 1 / 2,
    prior_variance: float = 1 / 4,
    fake_obs: int = 1,
    scale: float = 1,
) -> RealArray:
    t = np.arange(1, len(x) + 1)
    mu_hat_t = np.minimum((fake_obs * prior_mean + np.cumsum(x)) / (t + fake_obs), 1)
    sigma2_t = (fake_obs * prior_variance + np.cumsum(np.power(x - mu_hat_t, 2))) / (t + fake_obs)
    sigma2_tminus1 = np.append(prior_variance, sigma2_t[0 : (len(x) - 1)])

    if fixed_n is None:
        lambdas = np.sqrt(2 * np.log(1 / alpha) / (t * np.log(1 + t) * sigma2_tminus1))
    else:
        lambdas = np.sqrt(2 * np.log(1 / alpha) / (fixed_n * sigma2_tminus1))

    lambdas[np.isnan(lambdas)] = 0
    lambdas = np.minimum(truncation, lambdas)
    return lambdas * scale


def _predmix_lower_cs(
    x: RealArray,
    v: RealArray,
    lambdas_fn: Callable[[RealArray], RealArray],
    psi_fn: Callable[[RealArray], RealArray],
    alpha: float = 0.05,
    running_intersection: bool = False,
) -> RealArray:
    t = np.arange(1, len(x) + 1)
    S_t = np.cumsum(x)
    lambdas = lambdas_fn(x)
    psi = psi_fn(lambdas)
    margin = (np.log(1 / alpha) + np.cumsum(v * psi)) / np.cumsum(lambdas)
    weighted_mu_hat_t = np.cumsum(lambdas * x) / np.cumsum(lambdas)
    l = np.maximum(weighted_mu_hat_t - margin, 0)
    return np.maximum.accumulate(l) if running_intersection else l


def _predmix_empbern_lower_cs(
    x: RealArray,
    alpha: float = 0.05,
    truncation: float = 1 / 2,
    running_intersection: bool = False,
    fixed_n: Optional[int] = None,
) -> RealArray:
    t = np.arange(1, len(x) + 1)
    mu_hat_t = np.cumsum(x) / t
    mu_hat_tminus1 = np.append(0, mu_hat_t[0 : (len(x) - 1)])
    v = np.power(x - mu_hat_tminus1, 2)
    return _predmix_lower_cs(
        x,
        v=v,
        lambdas_fn=lambda y: _lambda_predmix_eb(y, truncation=truncation, alpha=alpha, fixed_n=fixed_n),
        psi_fn=lambda lambdas: -np.log(1 - lambdas) - lambdas,
        alpha=alpha,
        running_intersection=running_intersection,
    )


def predmix_empbern_twosided_cs(
    x: RealArray,
    alpha: float = 0.05,
    truncation: float = 1 / 2,
    running_intersection: bool = True,
) -> tuple[RealArray, RealArray]:
    """Two-sided predictable-mixture empirical-Bernstein confidence
    sequence for the mean of `x`, a sequence of observations in [0, 1]
    (here: binary ground-truth violation labels). Returns `(lower, upper)`
    arrays, one bound per prefix length — valid *simultaneously* at every
    prefix length, not just the one it's evaluated at, which is what makes
    it safe to check after every new finding rather than only at a
    pre-planned sample size.
    """
    x = np.asarray(x, dtype=float)
    lower = _predmix_empbern_lower_cs(
        x, alpha=alpha / 2, truncation=truncation, running_intersection=running_intersection
    )
    upper = 1 - _predmix_empbern_lower_cs(
        1 - x, alpha=alpha / 2, truncation=truncation, running_intersection=running_intersection
    )
    return lower, upper
