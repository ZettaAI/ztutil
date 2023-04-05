# pylint: disable=missing-docstring
from __future__ import annotations

import ast
from copy import deepcopy
from typing import Any, Dict, Literal, Optional, Union, overload

import attrs
import cachetools
import numpy as np
import tensorstore
import torch
from typeguard import suppress_type_checks

from zetta_utils import tensor_ops
from zetta_utils.common import abspath
from zetta_utils.geometry import Vec3D

from .. import VolumetricBackend, VolumetricIndex
from ..cloudvol import CVBackend
from ..layer_set import VolumetricSetBackend
from ..precomputed import InfoExistsModes, PrecomputedInfoSpec

_ts_cache: cachetools.LRUCache = cachetools.LRUCache(maxsize=16)
_ts_cached: Dict[str, set] = {}

IN_MEM_CACHE_NUM_BYTES_PER_TS = 128 * 1024 ** 2

# TODO: Use `assume_metadata` off of the cached info, using `get_info`.
# Cannot use regular hashkey as the resolutions used need to be tracked
def _get_ts_at_resolution(
    path: str, cache_bytes_limit: Optional[int] = None, resolution: Optional[str] = None
) -> tensorstore.TensorStore:
    if cache_bytes_limit is None:
        cache_bytes_limit = IN_MEM_CACHE_NUM_BYTES_PER_TS
    if (path, resolution) in _ts_cache:
        return _ts_cache[path, resolution]
    spec: Dict[str, Any] = {
        "driver": "neuroglancer_precomputed",
        "kvstore": abspath(path),
        "context": {"cache_pool": {"total_bytes_limit": cache_bytes_limit}},
        "recheck_cached_data": "open",
    }
    if resolution is not None:
        spec["scale_metadata"] = {"resolution": ast.literal_eval(resolution)}
    result = tensorstore.open(spec).result()
    _ts_cache[(path, resolution)] = result
    if path not in _ts_cached:
        _ts_cached[path] = set()
    _ts_cached[path].add(resolution)
    return result


def _clear_ts_cache(path: str) -> None:
    resolutions = _ts_cached.pop(path, None)
    if resolutions is not None:
        for resolution in resolutions:
            _ts_cache.pop((path, resolution))


@attrs.mutable
class TSBackend(VolumetricBackend):  # pylint: disable=too-few-public-methods
    """
    Backend for peforming IO on Neuroglancer datasts using TensorStore library.
    Read data will be a ``torch.Tensor`` in ``CXYZ`` dimension order.
    Write data is expected to be a ``torch.Tensor`` or ``np.ndarray`` in ``CXYZ``
    dimension order.
    :param path: Precomputed path.
    :param info_spec: Specification for the info file for the layer. If None, the
        info is assumed to exist.
    :param on_info_exists: Behavior mode for when both `info_spec` is given and
        the layer info already exists.

    """

    path: str
    info_spec: Optional[PrecomputedInfoSpec] = None
    on_info_exists: InfoExistsModes = "expect_same"
    cache_bytes_limit: Optional[int] = None

    def __attrs_post_init__(self):
        if self.info_spec is None:
            self.info_spec = PrecomputedInfoSpec()
        overwritten = self.info_spec.update_info(self.path, self.on_info_exists)
        if overwritten:
            _clear_ts_cache(self.path)

    @overload
    @staticmethod
    def from_precomputed(backend: TSBackend) -> TSBackend:
        ...

    @overload
    @staticmethod
    def from_precomputed(backend: CVBackend) -> TSBackend:
        ...

    @overload
    @staticmethod
    def from_precomputed(backend: VolumetricSetBackend) -> VolumetricSetBackend:
        ...

    @overload
    @staticmethod
    def from_precomputed(backend: VolumetricBackend) -> VolumetricBackend:
        ...

    @staticmethod
    def from_precomputed(backend):
        if isinstance(backend, CVBackend):
            return TSBackend(backend.path, backend.info_spec, backend.on_info_exists)
        elif isinstance(backend, VolumetricSetBackend):
            return attrs.evolve(
                backend,
                layers={
                    k: attrs.evolve(v, backend=TSBackend.from_precomputed(v.backend))
                    for k, v in backend.layers.items()
                },
            )
        return backend  # pragma: no cover

    @property
    def name(self) -> str:  # pragma: no cover
        return self.path

    @name.setter
    def name(self, name: str) -> None:  # pragma: no cover
        raise NotImplementedError(
            "cannot set `name` for CVBackend directly;"
            " use `backend.with_changes(name='name')` instead."
        )

    @property
    def dtype(self) -> torch.dtype:
        try:
            result = _get_ts_at_resolution(self.path, self.cache_bytes_limit)
            dtype = result.dtype.name
            return getattr(torch, dtype)
        except Exception as e:
            raise e

    @property
    # TODO: Figure out a way to access 'multiscale metadata' directly
    def num_channels(self) -> int:  # pragma: no cover
        result = _get_ts_at_resolution(self.path, self.cache_bytes_limit)
        return result.shape[-1]

    @property
    def is_local(self) -> bool:  # pragma: no cover
        return self.path.startswith("file://")

    @property
    def enforce_chunk_aligned_writes(self) -> bool:  # pragma: no cover
        return False

    @enforce_chunk_aligned_writes.setter
    def enforce_chunk_aligned_writes(self, value: bool) -> None:  # pragma: no cover
        raise NotImplementedError(
            "cannot set `enforce_chunk_aligned_writes` for TSBackend; can only be set to `False`"
        )

    @property
    def allow_cache(self) -> bool:  # pragma: no cover
        return True

    @allow_cache.setter
    def allow_cache(self, value: Union[bool, str]) -> None:  # pragma: no cover
        raise NotImplementedError(
            "cannot set `allow_cache` for CVBackend directly;"
            " use `backend.with_changes(allow_cache=value:Union[bool, str])` instead."
        )

    @property
    def use_compression(self) -> bool:  # pragma: no cover
        return False

    @use_compression.setter
    def use_compression(self, value: bool) -> None:  # pragma: no cover
        raise NotImplementedError(
            "cannot set `use_compression` for TSBackend; can only be set to `False`"
        )

    def clear_cache(self) -> None:  # pragma: no cover
        _clear_ts_cache(self.path)

    def read(self, idx: VolumetricIndex) -> torch.Tensor:
        # Data out: cxyz
        ts = _get_ts_at_resolution(self.path, self.cache_bytes_limit, str(list(idx.resolution)))

        with suppress_type_checks():
            bounds = self.get_bounds(idx.resolution)
            idx_inbounds = bounds.intersection(idx)

        data_raw = np.array(ts[idx_inbounds.to_slices()])

        if idx_inbounds != idx:
            with suppress_type_checks():
                _, subindex = bounds.get_intersection_and_subindex(idx)
            data_final = np.zeros_like(data_raw, shape=list(idx.shape) + [data_raw.shape[-1]])
            data_final[subindex] = data_raw[:, :, :]
        else:
            data_final = data_raw

        result_np = np.transpose(data_final, (3, 0, 1, 2))
        result = tensor_ops.to_torch(result_np)
        return result

    def write(self, idx: VolumetricIndex, data: torch.Tensor):
        # Data in: cxyz
        # Write format: xyzc (b == 1)
        data_np = tensor_ops.convert.to_np(data)
        if data_np.size == 1 and len(data_np.shape) == 1:
            data_final = data_np[0]
        elif len(data_np.shape) == 4:
            data_final = np.transpose(data_np, (1, 2, 3, 0))
        else:
            raise ValueError(
                "Data written to CloudVolume backend must be in cxyz` dimension format, "
                f"but got a tensor of with ndim == {data_np.ndim}"
            )

        ts = _get_ts_at_resolution(self.path, self.cache_bytes_limit, str(list(idx.resolution)))
        slices = idx.to_slices()
        ts[slices] = data_final

    def with_changes(self, **kwargs) -> TSBackend:
        """Currently untyped. Supports:
        "name" = value: str
        "allow_cache" = value: Union[bool, str] - must be False for TensorStoreBackend, ignored
        "enforce_chunk_aligned_writes" = value: bool - must be False for TensorStoreBackend
        "voxel_offset_res" = (voxel_offset, resolution): Tuple[Vec3D[int], Vec3D]
        "chunk_size_res" = (chunk_size, resolution): Tuple[Vec3D[int], Vec3D]
        """
        # TODO: implement proper allow_cache logic
        assert self.info_spec is not None

        info_spec = deepcopy(self.info_spec)

        implemented_keys = [
            "name",
            "allow_cache",
            "enforce_chunk_aligned_writes",
            "voxel_offset_res",
            "chunk_size_res",
        ]
        keys_to_kwargs = {"name": "path"}
        keys_to_infospec_fn = {
            "voxel_offset_res": info_spec.set_voxel_offset,
            "chunk_size_res": info_spec.set_chunk_size,
        }
        keys_to_assert = {"enforce_chunk_aligned_writes": False}
        evolve_kwargs = {}
        for k, v in kwargs.items():
            if k not in implemented_keys:
                raise KeyError(f"key `{k}` received, expected one of `{implemented_keys}`")
            if k in keys_to_kwargs:
                evolve_kwargs[keys_to_kwargs[k]] = v
            if k in keys_to_infospec_fn:
                keys_to_infospec_fn[k](v)
            if k in keys_to_assert:
                if v != keys_to_assert[k]:
                    raise ValueError(
                        f"key `{k}` received with value `{v}`, but is required to be "
                        f"`{keys_to_assert[k]}`"
                    )
        # must clear the TS cache since the TS cache is separate from the info cache
        _clear_ts_cache(self.path)
        if "name" in kwargs:
            _clear_ts_cache(kwargs["name"])

        return attrs.evolve(
            self,
            **evolve_kwargs,
            info_spec=info_spec,
            on_info_exists="overwrite",
        )

    def get_voxel_offset(self, resolution: Vec3D) -> Vec3D[int]:
        ts = _get_ts_at_resolution(self.path, self.cache_bytes_limit, str(list(resolution)))
        return Vec3D[int](*ts.chunk_layout.grid_origin[0:3])

    def get_chunk_size(self, resolution: Vec3D) -> Vec3D[int]:
        ts = _get_ts_at_resolution(self.path, self.cache_bytes_limit, str(list(resolution)))
        return Vec3D[int](*ts.chunk_layout.read_chunk.shape[0:3])

    # TODO: implement the following two methods for VolumetricBackendProtocol
    def get_size(self, resolution: Vec3D) -> Vec3D[int]:  # pragma: no cover
        ts = _get_ts_at_resolution(self.path, self.cache_bytes_limit, str(list(resolution)))
        return Vec3D[int](*ts.shape[0:3])

    def get_bounds(self, resolution: Vec3D) -> VolumetricIndex:  # pragma: no cover
        offset = self.get_voxel_offset(resolution)
        size = self.get_size(resolution)
        return VolumetricIndex.from_coords(offset, offset + size, resolution)

    def get_chunk_aligned_index(  # pragma: no cover
        self, idx: VolumetricIndex, mode: Literal["expand", "shrink", "round"]
    ) -> VolumetricIndex:
        offset = self.get_voxel_offset(idx.resolution) * idx.resolution
        chunk_size = self.get_chunk_size(idx.resolution) * idx.resolution
        if mode != "expand" and mode != "shrink":  # pylint:disable=consider-using-in
            raise NotImplementedError(
                f"TensorStore backend only supports 'expand' or 'shrink' modes; received '{mode}'"
            )
        bbox_aligned = idx.bbox.snapped(offset, chunk_size, mode)
        return VolumetricIndex(resolution=idx.resolution, bbox=bbox_aligned)

    def assert_idx_is_chunk_aligned(self, idx: VolumetricIndex) -> None:  # pragma: no cover
        """check that the idx given is chunk_aligned, and give suggestions"""
        idx_expanded = self.get_chunk_aligned_index(idx, mode="expand")
        idx_shrunk = self.get_chunk_aligned_index(idx, mode="shrink")

        if idx != idx_expanded:
            raise ValueError(
                "The specified BBox3D is not chunk-aligned with the VolumetricLayer at"
                + f" `{self.name}`;\nin {tuple(idx.resolution)} {idx.bbox.unit} voxels:"
                + f" offset: {self.get_voxel_offset(idx.resolution)},"
                + f" chunk_size: {self.get_chunk_size(idx.resolution)}\n"
                + f"Received BBox3D: {idx.pformat()}\n"
                + "Nearest chunk-aligned BBox3Ds:\n"
                + f" - expanded : {idx_expanded.pformat()}\n"
                + f" - shrunk   : {idx_shrunk.pformat()}"
            )

    def pformat(self) -> str:  # pragma: no cover
        return self.name
