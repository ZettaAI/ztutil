import math
from typing import Optional, Tuple
import attrs

from typeguard import typechecked

from zetta_utils import builder
from zetta_utils.log import logger
from zetta_utils.training.datasets.sample_indexers import SampleIndexer
from zetta_utils.typing import Vec3D
from zetta_utils.bbox import BoundingCube


@builder.register("VolumetricStepIndexer")
@typechecked
@attrs.frozen
class VolumetricStepIndexer(SampleIndexer):
    """Indexer which takes samples from a volumetric region at uniform intervals.

    :param bcube: Bounding cube representing the whole volume to be indexed.
    :param sample_size: Size of a training sample.
    :param sample_size_resolution: Resoluiton at which ``sample_size`` is given.
    :param step_size: Distance between neighboring samples along each dimension.
    :param step_size_resolution: Resoluiton at which ``step_size`` is given.
    :param index_resolution: Resoluiton at at which to form an index for each sample.
    :param desired_resolution: Desired resoluiton which will be indicated as a part
        of index for each sample. When ``desired_resolution is None``, no desired
        resolution will be specified in the index.

    """

    bcube: BoundingCube
    sample_size: Vec3D
    sample_size_resolution: Vec3D
    step_size: Vec3D
    step_size_resolution: Vec3D
    index_resolution: Vec3D
    desired_resolution: Optional[Vec3D] = None
    sample_size_in_unit: Vec3D = attrs.field(init=False)
    step_size_in_unit: Vec3D = attrs.field(init=False)
    step_limits: Tuple[int, int, int] = attrs.field(init=False)

    def __attrs_post_init__(self):
        bcube_size_in_unit = tuple(
            self.bcube.bounds[i][1] - self.bcube.bounds[i][0] for i in range(3)
        )
        sample_size_in_unit = tuple(
            s * r for s, r in zip(self.sample_size, self.sample_size_resolution)
        )
        step_size_in_unit = tuple(s * r for s, r in zip(self.step_size, self.step_size_resolution))
        step_limits_raw = tuple(
            (b - s) / st + 1
            for b, s, st in zip(
                bcube_size_in_unit,
                sample_size_in_unit,
                step_size_in_unit,
            )
        )
        step_limits = tuple(math.floor(e) for e in step_limits_raw)

        if step_limits != step_limits_raw:
            rounded_bcube_bounds = tuple(
                (
                    self.bcube.bounds[i][0],
                    (
                        self.bcube.bounds[i][0]
                        + sample_size_in_unit[i]
                        + (step_limits[i] - 1) * step_size_in_unit[i]
                    ),
                )
                for i in range(3)
            )
            logger.warning(
                f"Rounding down bcube bounds from {self.bcube.bounds} to {rounded_bcube_bounds} "
                f"to divide evenly by step size {step_size_in_unit}{self.bcube.unit} "
                f"with sample size {sample_size_in_unit}{self.bcube.unit}."
            )

        # Use `__setattr__` to keep the object frozen.
        object.__setattr__(self, "step_limits", step_limits)
        object.__setattr__(self, "sample_size_in_unit", sample_size_in_unit)
        object.__setattr__(self, "step_size_in_unit", step_size_in_unit)

    def __len__(self):
        result = self.step_limits[0] * self.step_limits[1] * self.step_limits[2]
        return result

    def __call__(self, idx: int) -> Tuple[Optional[Vec3D], slice, slice, slice]:
        """Translate a sample index to a volumetric region in space.

        :param idx: Integer sample index.
        :return: Volumetric index for the training sample patch, including
            ``self.desired_resolution`` and the slice representation of the region
            at ``self.index_resolution``.

        """
        steps_along_dim = [
            idx % self.step_limits[0],
            (idx // self.step_limits[0]) % self.step_limits[1],
            (idx // (self.step_limits[0] * self.step_limits[1])) % self.step_limits[2],
        ]
        sample_origin_in_unit = [
            self.bcube.bounds[i][0] + self.step_size_in_unit[i] * steps_along_dim[i]
            for i in range(3)
        ]
        sample_end_in_unit = [
            origin + size for origin, size in zip(sample_origin_in_unit, self.sample_size_in_unit)
        ]
        slices = tuple(
            slice(origin // res, end // res)
            for origin, end, res in zip(
                sample_origin_in_unit, sample_end_in_unit, self.index_resolution
            )
        )
        result = (self.desired_resolution, slices[0], slices[1], slices[2])
        return result
