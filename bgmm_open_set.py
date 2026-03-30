from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
from sklearn.mixture import BayesianGaussianMixture
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class PredictionResult:
    """Container for single-sample open-set prediction results."""

    predicted_class: Optional[int]
    is_unknown: bool
    memberships: Dict[int, float]
    id_score: float


class BGMMCosineOpenSetRecognizer:
    """
    Open-set recognizer based on class-wise BGMM prototypes + cosine similarity.

    Workflow:
    1) Train one BayesianGaussianMixture per class.
    2) Use the component means as subclass centers (optionally filtered by weight).
    3) For a test sample, compute cosine similarity to all subclass centers in each class.
    4) Use the max similarity of each class as class membership.
    5) Use the global max membership as ID score.
    6) Compare ID score with threshold for unknown detection.
    """

    def __init__(
        self,
        n_components: int = 8,
        threshold: float = 0.5,
        weight_concentration_prior_type: str = "dirichlet_process",
        covariance_type: str = "full",
        max_iter: int = 300,
        random_state: Optional[int] = 42,
        weight_threshold: float = 1e-3,
        bgmm_kwargs: Optional[dict] = None,
    ) -> None:
        self.n_components = n_components
        self.threshold = threshold
        self.weight_concentration_prior_type = weight_concentration_prior_type
        self.covariance_type = covariance_type
        self.max_iter = max_iter
        self.random_state = random_state
        self.weight_threshold = weight_threshold
        self.bgmm_kwargs = bgmm_kwargs or {}

        self.class_models_: Dict[int, BayesianGaussianMixture] = {}
        self.class_centers_: Dict[int, np.ndarray] = {}
        self.classes_: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None

    def fit(self, X: np.ndarray, y: Sequence[int]) -> "BGMMCosineOpenSetRecognizer":
        """Fit one BGMM per class from feature vectors X and labels y."""
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)

        if X.ndim != 2:
            raise ValueError("X must be a 2D array: (n_samples, n_features)")
        if y.ndim != 1:
            raise ValueError("y must be a 1D array: (n_samples,)")
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y must have the same number of samples")

        self.classes_ = np.unique(y)
        self.n_features_in_ = X.shape[1]
        self.class_models_.clear()
        self.class_centers_.clear()

        for cls in self.classes_:
            X_cls = X[y == cls]
            if X_cls.shape[0] < 2:
                raise ValueError(f"Class {cls} has fewer than 2 samples; cannot fit BGMM reliably")

            model = BayesianGaussianMixture(
                n_components=self.n_components,
                weight_concentration_prior_type=self.weight_concentration_prior_type,
                covariance_type=self.covariance_type,
                max_iter=self.max_iter,
                random_state=self.random_state,
                **self.bgmm_kwargs,
            )
            model.fit(X_cls)

            weights = model.weights_
            means = model.means_
            active_mask = weights > self.weight_threshold
            active_centers = means[active_mask]
            if active_centers.shape[0] == 0:
                active_centers = means[[int(np.argmax(weights))]]

            self.class_models_[int(cls)] = model
            self.class_centers_[int(cls)] = active_centers

        return self

    def _check_is_fitted(self) -> None:
        if self.classes_ is None or self.n_features_in_ is None:
            raise RuntimeError("Model is not fitted. Call fit(X, y) first.")

    def _compute_memberships(self, x: np.ndarray) -> Dict[int, float]:
        """Compute max cosine similarity to subclass centers for each class."""
        memberships: Dict[int, float] = {}
        x_2d = x.reshape(1, -1)

        for cls, centers in self.class_centers_.items():
            sims = cosine_similarity(x_2d, centers)[0]
            memberships[cls] = float(np.max(sims))

        return memberships

    def predict_one(self, x: np.ndarray) -> PredictionResult:
        """Predict class / unknown flag / memberships for one sample."""
        self._check_is_fitted()
        x = np.asarray(x, dtype=float)

        if x.ndim != 1:
            raise ValueError("x must be a 1D feature vector")
        if x.shape[0] != self.n_features_in_:
            raise ValueError(
                f"x feature dimension mismatch: got {x.shape[0]}, expected {self.n_features_in_}"
            )

        memberships = self._compute_memberships(x)
        predicted_class = max(memberships, key=memberships.get)
        id_score = memberships[predicted_class]
        is_unknown = id_score < self.threshold

        return PredictionResult(
            predicted_class=None if is_unknown else predicted_class,
            is_unknown=is_unknown,
            memberships=memberships,
            id_score=id_score,
        )

    def predict(self, X: np.ndarray) -> List[PredictionResult]:
        """Batch prediction for multiple samples."""
        self._check_is_fitted()
        X = np.asarray(X, dtype=float)

        if X.ndim != 2:
            raise ValueError("X must be a 2D array: (n_samples, n_features)")
        if X.shape[1] != self.n_features_in_:
            raise ValueError(
                f"X feature dimension mismatch: got {X.shape[1]}, expected {self.n_features_in_}"
            )

        return [self.predict_one(x) for x in X]


if __name__ == "__main__":
    # Minimal demo with synthetic features
    rng = np.random.RandomState(0)
    X0 = rng.normal(loc=[1.0, 0.0], scale=0.2, size=(100, 2))
    X1 = rng.normal(loc=[0.0, 1.0], scale=0.2, size=(100, 2))
    X_train = np.vstack([X0, X1])
    y_train = np.array([0] * len(X0) + [1] * len(X1))

    model = BGMMCosineOpenSetRecognizer(n_components=4, threshold=0.7, random_state=0)
    model.fit(X_train, y_train)

    X_test = np.array([
        [1.1, 0.1],   # likely class 0
        [0.2, 0.9],   # likely class 1
        [-1.0, -1.0], # likely unknown
    ])

    for i, res in enumerate(model.predict(X_test)):
        print(f"Sample {i}")
        print("  predicted_class:", res.predicted_class)
        print("  is_unknown:", res.is_unknown)
        print("  memberships:", res.memberships)
        print("  id_score:", res.id_score)
