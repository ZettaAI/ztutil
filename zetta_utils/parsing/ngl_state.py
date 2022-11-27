"""neuroglancer state parsing."""

from enum import Enum
from enum import Enum
from os import environ
from typing import List, Union

import numpy as np
import numpy as np
from cloudfiles import CloudFiles
from neuroglancer.viewer_state import (
    AnnotationLayer,
    AxisAlignedBoundingBoxAnnotation,
    PointAnnotation,
    make_layer,
)

from zetta_utils.bcube import BoundingCube
from zetta_utils.bcube.bcube import BoundingBoxND
from zetta_utils.log import get_logger
from zetta_utils.typing import Vec3D

logger = get_logger("zetta_utils")
remote_path = environ.get("REMOTE_LAYERS_PATH", "gs://remote-annotations")


class NGL_LAYER_KEYS(Enum):
    ANNOTATION_COLOR = "annotationColor"
    ANNOTATIONS = "annotations"
    NAME = "name"
    RESOLUTION = "voxelSize"
    TOOL = "tool"
    TYPE = "type"


class DEFAULT_LAYER_VALUES(Enum):
    COLOR = "#ff0000"
    TYPE = "annotation"
    TOOL = "annotateBoundingBox"


def load(layer_name: str) -> AnnotationLayer:
    from cloudfiles import CloudFiles
    from neuroglancer.viewer_state import make_layer


class NGL_LAYER_KEYS(Enum):
    ANNOTATION_COLOR = "annotationColor"
    ANNOTATIONS = "annotations"
    NAME = "name"
    RESOLUTION = "voxelSize"
    TOOL = "tool"
    TYPE = "type"


class ANNOTATION_KEYS(Enum):
    ID = "id"
    POINT = "point"
    POINT_A = "pointA"
    POINT_B = "pointB"
    TYPE = "type"


class DEFAULT_LAYER_VALUES(Enum):
    COLOR = "#ff0000"
    TYPE = "annotation"
    TOOL = "annotateBoundingBox"


def read_remote_annotations(layer_name: str) -> List[Union[BoundingCube, Vec3D]]:
    logger.info(f"Remote layer: {remote_path}/{layer_name}.")

    cf = CloudFiles(remote_path)
    layer_json = cf.get_json(layer_name)
    logger.debug(layer_json)
    layer: AnnotationLayer = make_layer(layer_json)

    logger.info(f"Layer type: {layer.type}; Total: {len(layer.annotations)}.")
    return _parse_annotations(layer)


def _parse_annotations(layer: AnnotationLayer) -> List[Union[BoundingCube, Vec3D]]:
    result: List[Union[BoundingCube, Vec3D]] = []
    resolution: Vec3D = layer.to_json()[NGL_LAYER_KEYS.RESOLUTION.value]
    for annotation in layer.annotations:
        assert isinstance(
            annotation, (AxisAlignedBoundingBoxAnnotation, PointAnnotation)
        ), "Annotation type not supported."
        try:
            bcube = BoundingCube.from_coords(
                annotation.point_a,
                annotation.point_b,
                resolution=resolution,
            )
            result.append(bcube)
        except AttributeError:
            point: Vec3D = annotation.point * resolution
            result.append(point)
    return result


def write_remote_annotations(
    layer_name: str,
    resolution: Vec3D,
    bcubes_or_points: List[Union[BoundingCube, Vec3D]],
) -> None:
    annotations = []
    layer_d = {
        NGL_LAYER_KEYS.NAME.value: layer_name,
        NGL_LAYER_KEYS.RESOLUTION.value: resolution,
        NGL_LAYER_KEYS.TOOL.value: DEFAULT_LAYER_VALUES.TOOL.value,
        NGL_LAYER_KEYS.TYPE.value: DEFAULT_LAYER_VALUES.TYPE.value,
        NGL_LAYER_KEYS.ANNOTATION_COLOR.value: DEFAULT_LAYER_VALUES.COLOR.value,
        NGL_LAYER_KEYS.ANNOTATIONS.value: annotations
    }

    for i, bcubes_or_point in enumerate(bcubes_or_points):
        if isinstance(bcubes_or_point, BoundingBoxND):
            x,y,z = bcubes_or_point.bounds
            point_a = np.array([x[0], y[0], z[0]])
            point_b = np.array([x[1], y[1], z[1]])
            annotation = {
                ANNOTATION_KEYS.ID.value: str(i),
                ANNOTATION_KEYS.POINT_A.value: point_a / resolution,
                ANNOTATION_KEYS.POINT_B.value: point_b / resolution,
                ANNOTATION_KEYS.TYPE.value: AxisAlignedBoundingBoxAnnotation().type
            }
            annotations.append(annotation)
        else:
            annotation = {
                ANNOTATION_KEYS.ID.value: str(i),
                ANNOTATION_KEYS.POINT.value: bcubes_or_point / resolution,
                ANNOTATION_KEYS.TYPE.value: PointAnnotation().type
            }
            annotations.append(annotation)
    layer = make_layer(layer_d)
    cf = CloudFiles(remote_path)
    cf.put_json(layer_name, layer.to_json())

    for i, bcubes_or_point in enumerate(bcubes_or_points):
        if isinstance(bcubes_or_point, BoundingBoxND):
            x,y,z = bcubes_or_point.bounds
            point_a = np.array([x[0], y[0], z[0]])
            point_b = np.array([x[1], y[1], z[1]])
            annotation = {
                ANNOTATION_KEYS.ID.value: str(i),
                ANNOTATION_KEYS.POINT_A.value: point_a / resolution,
                ANNOTATION_KEYS.POINT_B.value: point_b / resolution,
                ANNOTATION_KEYS.TYPE.value: AxisAlignedBoundingBoxAnnotation().type
            }
            annotations.append(annotation)
        else:
            annotation = {
                ANNOTATION_KEYS.ID.value: str(i),
                ANNOTATION_KEYS.POINT.value: bcubes_or_point / resolution,
                ANNOTATION_KEYS.TYPE.value: PointAnnotation().type
            }
            annotations.append(annotation)
    layer = make_layer(layer_d)
    cf = CloudFiles(remote_path)
    cf.put_json(layer_name, layer.to_json())