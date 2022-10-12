# pylint: disable=missing-docstring
from typing import Dict, Union, Callable, Any, Sequence
from typeguard import typechecked

from zetta_utils import builder
from zetta_utils.indexes import IndexAdjusterWithProcessors, Index

from .layer import Layer
from .layer_set_io_backend import LayerSetBackend


@typechecked
@builder.register("LayerSet")
def build_layer_set(
    layers: Dict[str, Layer],
    readonly: bool = False,
    index_adjs: Sequence[Union[Callable[..., Index], IndexAdjusterWithProcessors]] = (),
    read_postprocs: Sequence[Callable[..., Any]] = (),
    write_preprocs: Sequence[Callable[..., Any]] = (),
) -> Layer:
    """Build a layer representing a set of layers given as input.

    :param layers: Mapping from layer names to layers.
    :param readonly: Whether layer is read only.
    :param index_adjs: List of adjustors that will be applied to the index given by the user
        prior to IO operations.
    :param read_postprocs: List of processors that will be applied to the read data before
        returning it to the user.
    :param write_preprocs: List of processors that will be applied to the data given by
        the user before writing it to the backend.
    :return: Layer built according to the spec.

    """
    backend = LayerSetBackend(layers)

    result = Layer(
        io_backend=backend,
        readonly=readonly,
        index_adjs=index_adjs,
        read_postprocs=read_postprocs,
        write_preprocs=write_preprocs,
    )
    return result
