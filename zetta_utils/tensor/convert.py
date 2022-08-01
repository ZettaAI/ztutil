"""Type conversion functions."""
from __future__ import annotations

from typing import overload

import torch
import numpy as np
import numpy.typing as npt
from typeguard import typechecked

import zetta_utils as zu


@overload
def to_np(data: torch.Tensor) -> npt.NDArray:  # pragma: no cover
    ...


@overload
def to_np(data: npt.NDArray) -> npt.NDArray:  # pragma: no cover
    ...


@typechecked
def to_np(data: zu.typing.Tensor) -> npt.NDArray:
    """Convert the given tensor to :class:`numpy.ndarray`.

    :param data: Input tensor.
    :return: Input tensor in :class:`np.ndarray` format.

    """
    if isinstance(data, torch.Tensor):
        result = data.cpu().detach().numpy()
    else:
        assert isinstance(data, np.ndarray)
        result = data

    return result


@overload
def to_torch(data: torch.Tensor) -> torch.Tensor:  # pragma: no cover
    ...


@overload
def to_torch(data: npt.NDArray) -> torch.Tensor:  # pragma: no cover
    ...


@typechecked
def to_torch(data: zu.typing.Tensor) -> torch.Tensor:
    """Convert the given tensor to :class:`torch.Tensor`.

    :param data: Input tensor.
    :return: Input tensor in :class:`torch.Tensor` format.

    """
    if isinstance(data, torch.Tensor):
        result = data
    else:
        assert isinstance(data, np.ndarray)
        result = torch.from_numpy(data)

    return result


@overload
def astype(
    data: torch.Tensor, reference: zu.typing.Tensor
) -> torch.Tensor:  # pylint: disable=missing-docstring # pragma: no cover
    ...


@overload
def astype(
    data: npt.NDArray, reference: zu.typing.Tensor
) -> npt.NDArray:  # pylint: disable=missing-docstring # pragma: no cover
    ...


@typechecked
def astype(data: zu.typing.Tensor, reference: zu.typing.Tensor) -> zu.typing.Tensor:
    """Convert the given tensor to :class:`np.ndarray` or :class:`torch.Tensor`
    depending on the type of reference tensor.

    :param data: Input tensor.
    :param reference: Reference type tensor.
    :return: Input tensor converted to the reference type.

    """
    if isinstance(reference, torch.Tensor):
        result = zu.tensor.convert.to_torch(data)  # type: zu.typing.Tensor
    elif isinstance(reference, np.ndarray):
        result = zu.tensor.convert.to_np(data)
    return result
