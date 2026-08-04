"""Statistical primitives used by the toolbox."""

from .classification import auc_binary, leave_one_out_gfc_classification
from .functional import detrend_preserve_mean, fast_corr, inverse_pearson, roi_correlation_matrix
from .group import (
    chi_square_test,
    compare_correlation_coefficients,
    permutation_ttest,
    quantile_regression,
    ttest2_with_covariates,
)
from .regression import regress, regress_out

__all__ = [
    "auc_binary",
    "chi_square_test",
    "compare_correlation_coefficients",
    "detrend_preserve_mean",
    "fast_corr",
    "inverse_pearson",
    "leave_one_out_gfc_classification",
    "permutation_ttest",
    "quantile_regression",
    "regress",
    "regress_out",
    "roi_correlation_matrix",
    "ttest2_with_covariates",
]
