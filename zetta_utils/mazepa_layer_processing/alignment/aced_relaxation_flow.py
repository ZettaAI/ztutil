from __future__ import annotations

from typing import Literal, Optional

import attrs

from zetta_utils import alignment, builder, mazepa, tensor_ops
from zetta_utils.geometry import BBox3D, IntVec3D, Vec3D
from zetta_utils.layer.volumetric import (
    VolumetricIndex,
    VolumetricIndexChunker,
    VolumetricLayer,
    VolumetricLayerSet,
)

from ..common import build_chunked_volumetric_callable_flow_schema


@builder.register("build_get_match_offsets_naive_flow")
def build_get_match_offsets_naive_flow(
    chunk_size: IntVec3D,
    bbox: BBox3D,
    dst_resolution: Vec3D,
    non_tissue: VolumetricLayer,
    dst: VolumetricLayer,
    misalignment_mask_zm1: VolumetricLayer,
    misalignment_mask_zm2: Optional[VolumetricLayer] = None,
    misalignment_mask_zm3: Optional[VolumetricLayer] = None,
) -> mazepa.Flow:
    flow_schema = build_chunked_volumetric_callable_flow_schema(
        fn=alignment.aced_relaxation.get_aced_match_offsets_naive,
        chunker=VolumetricIndexChunker(chunk_size=chunk_size),
    )
    flow = flow_schema(
        idx=VolumetricIndex(bbox=bbox, resolution=dst_resolution),
        non_tissue=non_tissue,
        dst=dst,
        misalignment_mask_zm1=misalignment_mask_zm1,
        misalignment_mask_zm2=misalignment_mask_zm2,
        misalignment_mask_zm3=misalignment_mask_zm3,
    )
    return flow


@builder.register("AcedMatchOffsetOp")
@mazepa.taskable_operation_cls
@attrs.frozen
class AcedMatchOffsetOp:
    crop_pad: IntVec3D = IntVec3D(0, 0, 0)

    def get_input_resolution(self, dst_resolution: Vec3D) -> Vec3D:  # pylint: disable=no-self-use
        return dst_resolution

    def with_added_crop_pad(self, crop_pad: IntVec3D) -> AcedMatchOffsetOp:
        return attrs.evolve(self, crop_pad=self.crop_pad + crop_pad)

    def __call__(
        self,
        idx: VolumetricIndex,
        dst: VolumetricLayerSet,
        tissue_mask: VolumetricLayer,
        misalignment_masks: dict[str, VolumetricLayer],
        pairwise_fields: dict[str, VolumetricLayer],
        pairwise_fields_inv: dict[str, VolumetricLayer],
        max_dist: int,
    ):
        idx_padded = idx.padded(self.crop_pad)
        result = alignment.aced_relaxation.get_aced_match_offsets(
            tissue_mask=tissue_mask[idx_padded],
            misalignment_masks={k: v[idx_padded] for k, v in misalignment_masks.items()},
            pairwise_fields={k: v[idx_padded] for k, v in pairwise_fields.items()},
            pairwise_fields_inv={k: v[idx_padded] for k, v in pairwise_fields_inv.items()},
            max_dist=max_dist,
        )
        result = {k: tensor_ops.crop(v, self.crop_pad) for k, v in result.items()}
        dst[idx] = result


@builder.register("build_aced_relaxation_flow")
def build_aced_relaxation_flow(
    chunk_size: IntVec3D,
    bbox: BBox3D,
    dst_resolution: Vec3D,
    dst: VolumetricLayer,
    match_offsets: VolumetricLayer,
    field_zm1: VolumetricLayer,
    crop_pad: IntVec3D,
    rigidity_masks: Optional[VolumetricLayer] = None,
    field_zm2: Optional[VolumetricLayer] = None,
    field_zm3: Optional[VolumetricLayer] = None,
    num_iter: int = 100,
    lr: float = 0.3,
    rigidity_weight: float = 10.0,
    fix: Optional[Literal["first", "last", "both"]] = "first",
) -> mazepa.Flow:
    flow_schema = build_chunked_volumetric_callable_flow_schema(
        fn=alignment.aced_relaxation.perform_aced_relaxation,
        chunker=VolumetricIndexChunker(chunk_size=chunk_size),
        crop_pad=crop_pad,
    )
    flow = flow_schema(
        idx=VolumetricIndex(bbox=bbox, resolution=dst_resolution),
        dst=dst,
        match_offsets=match_offsets,
        rigidity_masks=rigidity_masks,
        field_zm1=field_zm1,
        field_zm2=field_zm2,
        field_zm3=field_zm3,
        num_iter=num_iter,
        lr=lr,
        rigidity_weight=rigidity_weight,
        fix=fix,
    )
    return flow
