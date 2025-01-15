"""
This script takes a set of mitochondria, and outputs line annotations which can be applied
to merge the mitochondria into its parent cell.  In cases where a mito has *two* parent
cells (e.g., it has caused a split), this will also merge those parents together.
"""

"""
This script prototypes a process for finding contacts between known presynaptic
cells in a smallish cutout, and any other cells in that cutout.
"""
import csv
import os
import sys
from datetime import datetime
from math import floor, sqrt
from typing import List, Optional, Sequence

import cc3d
import cv2
import google.auth
import nglui
import numpy as np
import torch
from caveclient import CAVEclient
from scipy.ndimage import binary_dilation

from zetta_utils.geometry import BBox3D, Vec3D
from zetta_utils.layer.volumetric import VolumetricIndex, VolumetricLayer
from zetta_utils.layer.volumetric.cloudvol import build_cv_layer
from zetta_utils.layer.volumetric.precomputed import PrecomputedInfoSpec

client: CAVEclient
ng_state = None


def distance_transform_fast(mask_3d):
    """
    This function is similary to scipy.ndimage.distance_transform_edt, except:
     1. It computes Manhattan distance, not Euclidean
     2. It runs much faster (especially on GPU, but even on CPU).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    mask_tensor = torch.tensor(~mask_3d, dtype=torch.float32, device=device)
    distance = torch.full_like(mask_tensor, float("inf"), device=device)
    distance[mask_tensor == 1] = 0

    shifts = [
        (1, 0, 0),
        (-1, 0, 0),
        (0, 1, 0),
        (0, -1, 0),
        (0, 0, 1),
        (0, 0, -1),
    ]

    for _ in range(max(mask_3d.shape)):  # Enough iterations to cover the full mask
        updated_distance = distance.clone()
        for dz, dy, dx in shifts:
            shifted = torch.roll(distance, shifts=(dz, dy, dx), dims=(0, 1, 2))
            updated_distance = torch.minimum(updated_distance, shifted + 1)
        if torch.equal(updated_distance, distance):
            break  # no more change; operation has converged
        distance = updated_distance

    return distance.cpu().numpy()


def verify_cave_auth():
    global client
    client = CAVEclient()
    try:
        client.state
        return  # no exception?  All's good!
    except:
        pass
    print("Authentication needed.")
    print("Go to: https://global.daf-apis.com/auth/api/v1/create_token")
    token = input("Enter token: ")
    client.auth.save_token(token=token)


def input_or_default(prompt: str, value: str) -> str:
    response = input(f"{prompt} [{value}]: ")
    if response == "":
        response = value
    return response


def get_annotation_layer_name(state, label: str = "synapse annotation") -> str:
    names = nglui.parser.annotation_layers(state)
    if len(names) == 0:
        print("No annotation layers found in this state.")
        sys.exit()
    elif len(names) == 1:
        return names[0]
    while True:
        for i in range(0, len(names)):
            print(f"{i+1}. {names[i]}")
        choice: int | str = input(f"Enter {label} layer name or number: ")
        if choice in names:
            return str(choice)
        choice = int(choice) - 1
        if choice >= 0 and choice < len(names):
            return names[choice]


def unarchived_segmentation_layers(state) -> List[str]:
    names = nglui.parser.segmentation_layers(state)
    for i in range(len(names) - 1, -1, -1):
        if nglui.parser.get_layer(state, names[i]).get("archived", False):
            del names[i]
    return names


def get_segmentation_layer_name(state, label: str = "cell segmentation") -> str:
    names = unarchived_segmentation_layers(state)
    if len(names) == 0:
        print("No segmentation layers found in this state.")
        sys.exit()
    elif len(names) == 1:
        return names[0]
    while True:
        for i in range(0, len(names)):
            print(f"{i+1}. {names[i]}")
        choice: int | str = input(f"Enter {label} layer name or number: ")
        if choice in names:
            return str(choice)
        choice = int(choice) - 1
        if choice >= 0 and choice < len(names):
            return names[choice]


def get_bounding_box(precomputed_path: str, scale_index=0) -> VolumetricIndex:
    """
    Given a path to a precomputed volume, return a VolumetricIndex describing the data bounds
    and the data resolution.
    """
    spec = PrecomputedInfoSpec(reference_path=precomputed_path)
    disable_stdout()  # (following call spews Google warning sometimes)
    info = spec.make_info()
    enable_stdout()
    assert info is not None
    scale = info["scales"][scale_index]
    resolution = scale["resolution"]
    start_coord = scale["voxel_offset"]
    size = scale["size"]
    end_coord = [a + b for (a, b) in zip(start_coord, size)]
    bounds = VolumetricIndex.from_coords(start_coord, end_coord, resolution)
    return bounds


def load_volume(path: str, scale_index: int = 0, index_resolution: Sequence[float] | None = None):
    """
    Load a CloudVolume given the path, and optionally, which scale (resolution) is desired.
    Return the CloudVolume, and a VolumetricIndex describing the data bounds and resolution.
    """
    spec = PrecomputedInfoSpec(reference_path=path)
    disable_stdout()  # (following call spews Google warning sometimes)
    info = spec.make_info()
    enable_stdout()
    assert info is not None
    scale = info["scales"][scale_index]
    resolution = scale["resolution"]
    start_coord = scale["voxel_offset"]
    size = scale["size"]
    end_coord = [a + b for (a, b) in zip(start_coord, size)]
    if index_resolution is None:
        index_resolution = resolution
    cvl = build_cv_layer(
        path=path,
        allow_slice_rounding=True,
        default_desired_resolution=index_resolution,
        index_resolution=index_resolution,
        data_resolution=resolution,
        interpolation_mode=info["type"],
    )
    bounds = VolumetricIndex.from_coords(start_coord, end_coord, index_resolution)
    return cvl, bounds


def disable_stdout():
    sys.stdout = open(os.devnull, "w")


def enable_stdout():
    sys.stdout = sys.__stdout__


def find_contact_mask(cell_ids, cell1, cell2, n=2):
    """
    Find and return a mask of all the places that cell1 and cell2 come within n*2
    steps of each other (in X and Y), within the cell_ids array.
    """
    # Create binary masks for cell1 and cell2
    mask_cell1 = cell_ids == cell1
    mask_cell2 = cell_ids == cell2

    # Define the structuring element for dilation (only dilate in X and Y)
    structuring_element = np.ones((n * 2 + 1, n * 2 + 1, 1))

    # Dilate the masks
    dilated_mask_cell1 = binary_dilation(mask_cell1, structure=structuring_element)
    dilated_mask_cell2 = binary_dilation(mask_cell2, structure=structuring_element)

    # Find the intersection of the dilated masks
    intersection_mask = dilated_mask_cell1 & dilated_mask_cell2
    return intersection_mask


def find_contact_clusters(cell_ids, cell1, cell2, n=2):
    """
    Find and return labeled clusters of contact areas where cell1 and cell2
    come within n*2 steps of each other (in X and Y), within the cell_ids array.
    """
    mask = find_contact_mask(cell_ids, cell1, cell2, n)
    cc_labels = cc3d.connected_components(mask, connectivity=26)
    return cc_labels


def nearby_point(mask, external_point, interior_distance=5, alpha=0.9):
    """
    Return the point in m with a value of target_value, that is close
    to external_point, but at least interior_distance from the edge
    of the cluster (defined by target_value), if reasonably possible.

    This function works in both 2D and 3D.

    Parameters:
    - mask: matrix where true (1) values define the cluster
    - interior_distance: minimum distance from the edge of the cluster
    - external_point: tuple (x, y) of external point coordinates
    - alpha: mixing parameter between interior distance and proximity to external_point (0 to 1)

    Returns:
    - Tuple (x, y) of the chosen point's coordinates
    """
    distance_from_edge = distance_transform_fast(mask)
    valid_points = np.argwhere(mask)

    # We want to minimize both the difference between the actual edge
    # distance and the desired edge distance, AND the distance to
    # the external point.  Sum these, with the weighting factor alpha,
    # and then find the minimum.
    external_point = np.array(external_point)
    distances_to_point = np.linalg.norm(valid_points - external_point, axis=1)

    edge_distances = distance_from_edge[tuple(valid_points.T)]
    edge_dist_diffs = abs(edge_distances - interior_distance)

    scores = alpha * edge_dist_diffs + (1 - alpha) * distances_to_point

    best_index = np.argmin(scores)
    best_point = tuple(valid_points[best_index])
    print(
        f"Best point near {tuple(external_point)} is {tuple(best_point)}, "
        f"with dist from edge {edge_distances[best_index]} "
        f"for diff {edge_dist_diffs[best_index]}, "
        f"and dist to point {distances_to_point[best_index]}, "
        f"for score {scores[best_index]}"
    )
    return best_point


def get_ng_state():
    global ng_state
    global client
    if ng_state == None:
        verify_cave_auth()
        # Stored state URL be like:
        # https://spelunker.cave-explorer.org/#!middleauth+https://global.daf-apis.com/nglstate/api/v1/6704696916967424
        # ID is the last part of this.
        state_id = input_or_default("Neuroglancer state ID or URL", "5312699228487680")
        if "/" in state_id:
            state_id = state_id.split("/")[-1]

        ng_state = client.state.get_state_json(state_id)  # ID from end of NG state URL
    return ng_state


def load_cell_seg_layer():
    """
    Prompt the user (if needed) for NG state and segmentation layer name;
    return the CloudVolume and VolumetricIndex for that layer.
    """
    state = get_ng_state()
    cell_layer_name = get_segmentation_layer_name(state, "segmentation")
    cell_source = nglui.parser.get_layer(state, cell_layer_name)["source"]
    print(f"Loading cell segmentation data from:\n{cell_source}")
    cell_cvl, cell_index = load_volume(cell_source)
    return cell_cvl, cell_index


def load_mito_points():
    """
    Prompt the user (if needed) for NG state and annotation layer name;
    then return a list of the Vec3D coordinates of points in that layer.
    """
    state = get_ng_state()
    points_layer_name = get_annotation_layer_name(state, "mito points")
    points_layer = nglui.parser.get_layer(state, points_layer_name)
    result = []
    for item in points_layer["annotations"]:
        result.append(round(Vec3D(*item["point"])))
    return result


def process_one(mito_point: Vec3D, seg_layer, resolution: Vec3D):
    """
    Process one mitochondrion, assumed to be the segment that contains
    the given point.  Add lines between this segment and any neighboring
    ones (i.e. across any valid neighbor contacts).

    Returns a list of line annotation JSON entries.
    """
    print(f"Processing mito at {list(mito_point)}...")
    # We need to define a bounding box that is reasonably small (for performance),
    # but guaranteed to contain the full mitochondrion (for correctness).
    # This should be safe (at 16, 16, 40):
    halfSizeInNm = Vec3D(4096, 4096, 4096)
    halfSizeInVox = round(halfSizeInNm / resolution)
    idx = VolumetricIndex.from_coords(
        mito_point - halfSizeInVox, mito_point + halfSizeInVox, resolution
    )
    chunk = seg_layer[idx][0]
    relative_point = floor(halfSizeInVox)
    mito_id = chunk[relative_point[0], relative_point[1], relative_point[2]]

    # Approach: create a binary mask for the mitochondrion, dilate this by a
    # voxel or two, and use that to mask the chunk.  See what segment IDs are
    # left; those are the ones the mito touches.
    mito_mask = chunk == mito_id
    N = 1  # neighborhood size
    structuring_element = np.ones((N * 2 + 1, N * 2 + 1, 1))
    dilated_mask = binary_dilation(mito_mask, structure=structuring_element)
    boundary_mask = dilated_mask & (~mito_mask)
    boundary_area = np.sum(boundary_mask)
    print(f"   Mitochondrion segment ID: {mito_id}; surface area: {boundary_area}")
    neighbor_ids = chunk[boundary_mask]
    unique_ids, counts = np.unique(neighbor_ids, return_counts=True)
    result = []
    for id, count in zip(unique_ids, counts):
        if count < boundary_area * 0.10:
            continue  # too small; not a valid contact
        print(f"   Found contact ({count} voxels) with segment {id}")
        neighbor_point: Vec3D = Vec3D(*nearby_point(chunk == id, halfSizeInVox, 5, 0.95))
        close_mito_pt: Vec3D = Vec3D(*nearby_point(mito_mask, neighbor_point, 5, 0.8))
        offset = mito_point - halfSizeInVox
        neighbor_point += offset
        close_mito_pt += offset

        diff = neighbor_point - close_mito_pt
        dist = sqrt(diff.x ** 2 + diff.y ** 2 + diff.z ** 2)
        print(f"    Line: {tuple(close_mito_pt)} - {tuple(neighbor_point)}  (distance: {dist})")
        elems = [
            f'"pointA": {list(close_mito_pt)}',
            f'"pointB": {list(neighbor_point)}',
            '"type": "line"',
            f'"id": "{mito_id}{id}"',
            f'"description": "{mito_id} - {id}"',
        ]
        result.append("{" + ",".join(elems) + "}")
    return result


def main():
    os.system("clear")
    mito_points = load_mito_points()
    print(f"Loaded {len(mito_points)} mitochondria points")
    cell_cvl, cell_index = load_cell_seg_layer()

    resolution = round(cell_index.resolution)
    print(f"Working resolution: {list(resolution)}")

    lines = []
    for i, mito in enumerate(mito_points):
        print(f"({i}/{len(mito_points)}) ", end="")
        lines += process_one(mito, cell_cvl, resolution)

    print()
    print('"annotations": [')
    print(",\n".join(lines))
    print("],")


if __name__ == "__main__":
    main()
