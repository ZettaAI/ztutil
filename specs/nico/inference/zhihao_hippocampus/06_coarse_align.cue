import "math"

import "list"

#Z_SKIP_MAP: {
	for z in list.Range(24, 3994, 1) {
		"\(z)": int | *(z-1)
	}
}

#Z_SKIP_MAP: {
	// // START: 24
	// "37": 33,
	// "40": 38,
	// "44": 42,
	// "56": 54,
	// "58": 56,
	// "79": 67,
	// "86": 84,
	// "95": 91,
	// "107": 105,
	// // "110": 108,
	// // "112": 110,
	// // "114": 112,
	// // "116": 114,
	// // "118": 116,
	// // "121": 118,
	// // "123": 121,
	// "124": 108,  // PARTIAL / MISSING
	// "132": 130,  // PARTIAL
	// "160": 158,
	// "162": 160,
	// "191": 189,
	// "212": 208,
	// "275": 271,
	// "279": 277,  // PARTIAL
	// "284": 282,
	// "295": 288,
	// "339": 337,
	// "358": 356,
	// "381": 376,
	// "399": 397,
	// "403": 401,
	// "467": 465,
	// "621": 617,
	// "643": 637,
	// "669": 667,  // PARTIAL
	// "700": 698,
	// "725": 723,  // PARTIAL
	// "803": 773,
	// "825": 823,
	// "831": 829,  // PARTIAL
	// "927": 925,  // PARTIAL
	// "1204": 1202,
	// "1300": 1298,
	// "1325": 1323,
	// "1328": 1325,
	// "1356": 1350,
	// "1361": 1359,
	// "1364": 1362,
	// "1381": 1379,
	// "1386": 1383,
	// "1394": 1391,
	// "1419": 1416,
	// "1423": 1419,
	// "1432": 1430,
	// "1434": 1432,
	// "1446": 1439,
	// "1448": 1446,
	// "1451": 1448,
	// "1464": 1451,
	// "1479": 1464,
	// "1501": 1479,
	// "1505": 1503,
	// "1531": 1529,
	// "1557": 1550,
	// "1560": 1558,
	// "1564": 1560,
	// "1575": 1564,
	// "1578": 1575,
	// "1585": 1578,
	// "1594": 1585,
	// "1598": 1594,
	// "1641": 1639,
	// "1667": 1665,  // PARTIAL
	// "1730": 1720,
	// "1739": 1730,
	// "1750": 1745,
	// "1781": 1751,
	// "1787": 1785,
	// "1789": 1787,
	// "1791": 1789,
	// "1800": 1792,
	// "1802": 1800,
	// "1819": 1817,
	// "1927": 1925,
	// "1994": 1992,
	// "1997": 1995,
	// "2021": 2019,
	// "2031": 2029,
	// "2114": 2112, // PARTIAL
	// "2166": 2164,
	// "2175": 2173,
	// "2182": 2180,
	// "2198": 2196,
	"2740": 2236,
	// "2754": 2752,
	// "2764": 2762,
	// "2812": 2810,
	// "2826": 2824,
	// "2836": 2834,
	// "2876": 2874,
	// "2880": 2877,
	// "2882": 2880,
	// "2894": 2892,
	// "2956": 2954,
	// "2958": 2956,
	// "3049": 3041,
	// "3183": 3181,
	// "3210": 3208,
	// "3212": 3210,
	// "3275": 3273,
	// "3306": 3304,
	// "3313": 3311,
	// "3375": 3373,
	// "3452": 3450,
	// "3635": 3633,
	// "3726": 3723,
	// "3737": 3735,
	// "3773": 3771,
	// "3813": 3811,
	// "3876": 3874,
	// "3907": 3904,
	// // END: 3994
}

_ALIGN_PARAMS: {
	// "24576": {channel: -1, sm: 100, num_iter: 700, lr: 0.001, src_zeros_sm_mult: 1.0, tgt_zeros_sm_mult: 1.0},
	"12288": {channel: 1, sm: 100, num_iter: 700, lr: 0.001, src_zeros_sm_mult: 0.001, tgt_zeros_sm_mult: 0.001},
	"6144": {channel: 3, sm: 50, num_iter: 700, lr: 0.0025, src_zeros_sm_mult: 0.001, tgt_zeros_sm_mult: 0.001},
}


// INPUT
// #UNALIGNED_IMG_PATH:    "https://td.princeton.edu/sseung-test1/ca3-alignment-temp/full_section_imap4"
#UNALIGNED_ENC_PATH:    "gs://zetta-research-nico/hippocampus/low_res_enc_c4"
#RIGID_ENC_PATH:        "gs://zetta-research-nico/hippocampus/rigid_w_scale/low_res_enc_c4_rigid"
#AFFINE_ENC_PATH:       "gs://zetta-research-nico/hippocampus/pairwise/affine_w_scale_inv/low_res_enc_c4"
#AFFINE_FIELD_PATH:     "gs://zetta-research-nico/hippocampus/pairwise/affine_w_scale/field"
#AFFINE_INV_FIELD_PATH:     "gs://zetta-research-nico/hippocampus/pairwise/affine_w_scale_inv/field"

// OUTPUT
#COARSE_WO_AFFINE_FIELD_PATH: "gs://zetta-research-nico/hippocampus/pairwise/coarse_w_scale_wo_affine/field"
// #COARSE_WO_AFFINE_INV_FIELD_PATH: "gs://zetta-research-nico/hippocampus/pairwise/coarse_w_scale_wo_affine_inv/field"
#COARSE_FIELD_PATH:     "gs://zetta-research-nico/hippocampus/pairwise/coarse_w_scale/field"
#COARSE_INV_FIELD_PATH: "gs://zetta-research-nico/hippocampus/pairwise/coarse_w_scale_inv/field"
#COARSE_ENC_PATH:       "gs://zetta-research-nico/hippocampus/pairwise/coarse_w_scale_inv/low_res_enc_c4"

#DST_INFO_CHUNK_SIZE: [2048, 2048, 1] // Will automatically get truncated if dataset becomes too small
#MAX_TASK_SIZE: [8192, 8192, 1]
#REFERENCE_RES: [3, 3, 45]

#Z_RANGE: [2740, 2741]

#DATASET_BOUNDS: [
	[0 * #REFERENCE_RES[0], 524288 * #REFERENCE_RES[0]],  // [0 * #REFERENCE_RES[0], 1474560 * #REFERENCE_RES[0]],
	[0 * #REFERENCE_RES[1], 524288 * #REFERENCE_RES[1]],  // [0 * #REFERENCE_RES[1], 1474560 * #REFERENCE_RES[1]],
	[24 * #REFERENCE_RES[2], 3994 * #REFERENCE_RES[2]],
]

#ROI_BOUNDS: [
	[0 * #REFERENCE_RES[0], 524288 * #REFERENCE_RES[0]],
	[0 * #REFERENCE_RES[1], 524288 * #REFERENCE_RES[1]],
	[#Z_RANGE[0] * #REFERENCE_RES[2], #Z_RANGE[1] * #REFERENCE_RES[2]],
]

"@type":                "mazepa.execute_on_gcp_with_sqs"
worker_cluster_region:  "us-east1"
worker_cluster_project: "zetta-research"
worker_cluster_name:    "zutils-x3"
worker_image:           "us-east1-docker.pkg.dev/zetta-research/zutils/zetta_utils:nico_py3.9_20240306"
worker_resources: {
	"nvidia.com/gpu": "1"
}
worker_replicas: 200
local_test:      true
debug: true

target: {
	"@type": "mazepa.sequential_flow"
	stages: [
		{
			"@type": "mazepa.concurrent_flow"
			stages: [
				for z in list.Range(#Z_RANGE[0], #Z_RANGE[1], 1) {
					#COMPUTE_FIELD_TEMPLATE & {
						_z_offset: #Z_SKIP_MAP["\(z)"] - z
						_bounds: [
							[#ROI_BOUNDS[0][0], #ROI_BOUNDS[0][1]],
							[#ROI_BOUNDS[1][0], #ROI_BOUNDS[1][1]],
							[z * #REFERENCE_RES[2], (z+1) * #REFERENCE_RES[2]],
						]
					}
				},
			]
		},
		#COMPOSE_FIELD_TEMPLATE & {
			_bounds: #ROI_BOUNDS
			dst_resolution: [6144, 6144, 45]
		},
		#INVERT_FIELD_TEMPLATE & {
			_bounds: #ROI_BOUNDS
			dst_resolution: [6144, 6144, 45]
		},
		#WARP_ENC_TEMPLATE & {
			_bounds: #ROI_BOUNDS
			dst_resolution: [6144, 6144, 45]
		},
		#WARP_ENC_TEMPLATE & {
			_bounds: #ROI_BOUNDS
			dst_resolution: [12288, 12288, 45]
		}
	]
}




#STAGE_TMPL: {
	let max_chunk_size = [
		list.Min([#MAX_TASK_SIZE[0], math.Ceil((#ROI_BOUNDS[0][1]-#ROI_BOUNDS[0][0])/dst_resolution[0])]),
		list.Min([#MAX_TASK_SIZE[1], math.Ceil((#ROI_BOUNDS[1][1]-#ROI_BOUNDS[1][0])/dst_resolution[1])]),
		1,
	]
	"@type":        "ComputeFieldStage"
	dst_resolution: _
	processing_chunk_sizes: [max_chunk_size]
	processing_crop_pads: [[0, 0, 0]]
	fn: {
		"@type":  "align_with_online_finetuner"
		"@mode":  "partial"
		channel:  int
		sm:       int
		num_iter: int
		lr:       float
		src_zeros_sm_mult: number
		tgt_zeros_sm_mult: number
	}
}

#COMPUTE_FIELD_TEMPLATE: {
	_bounds: _ | *#ROI_BOUNDS
	_z_offset: int

	"@type": "build_compute_field_multistage_flow"
	bbox: {
		"@type": "BBox3D.from_coords"
		start_coord: [_bounds[0][0], _bounds[1][0], _bounds[2][0]]
		end_coord: [_bounds[0][1], _bounds[1][1], _bounds[2][1]]
	}
	stages: [
		// #STAGE_TMPL & {  // 24576
		// 	dst_resolution: [24576, 24576, #REFERENCE_RES[2]]
		// 	fn: #STAGE_TMPL.fn & _ALIGN_PARAMS["24576"]
		// },
		#STAGE_TMPL & {  // 12288
			dst_resolution: [12288, 12288, #REFERENCE_RES[2]]
			fn: #STAGE_TMPL.fn & _ALIGN_PARAMS["12288"]
		},
		#STAGE_TMPL & {  // 6144
			dst_resolution: [6144, 6144, #REFERENCE_RES[2]]
			fn: #STAGE_TMPL.fn & _ALIGN_PARAMS["6144"]
		},
	]

	tgt_offset: [0, 0, _z_offset]
	offset_resolution: #REFERENCE_RES

	src: {
		"@type": "build_cv_layer"
		path:    #AFFINE_ENC_PATH
		read_procs: [
			{"@type": "lambda", "lambda_str": "lambda x: torch.where(x[1:2,:,:,:] == -103, 0, x)"},
			// {"@type": "lambda", "lambda_str": "lambda x: torch.where(x[0:1,:,:,:] == -120, 0, x)"},
			// {"@type": "lambda", "lambda_str": "lambda x: torch.where(x[0:1,:,:,:] == 112, 0, x)"}
		]
	}
	tgt: {
		"@type": "build_cv_layer"
		path:    #RIGID_ENC_PATH
		read_procs: [
			{"@type": "lambda", "lambda_str": "lambda x: torch.where(x[1:2,:,:,:] == -103, 0, x)"},
			// {"@type": "lambda", "lambda_str": "lambda x: torch.where(x[0:1,:,:,:] == -120, 0, x)"},
			// {"@type": "lambda", "lambda_str": "lambda x: torch.where(x[0:1,:,:,:] == 112, 0, x)"}
		]
	}
	dst: {
		"@type": "build_cv_layer"
		path:    #COARSE_WO_AFFINE_FIELD_PATH
		info_reference_path: #AFFINE_FIELD_PATH
		info_add_scales: [[12288, 12288, 45], [24576, 24576, 45]]
		info_add_scales_mode: "merge"
		on_info_exists: "overwrite"
	}
	tmp_layer_dir: #COARSE_WO_AFFINE_FIELD_PATH + "/tmp"
	tmp_layer_factory: {
		"@type":              "build_cv_layer"
		"@mode":              "partial"
		info_reference_path:  #AFFINE_FIELD_PATH
		info_add_scales:     [[12288, 12288, 45], [24576, 24576, 45]]
		info_add_scales_mode: "merge"
		on_info_exists:       "overwrite"
	}
}

#COMPOSE_FIELD_TEMPLATE: {
	_bounds: _ | *#ROI_BOUNDS
	let max_chunk_size = [
		list.Min([#MAX_TASK_SIZE[0], math.Ceil((_bounds[0][1]-_bounds[0][0])/dst_resolution[0])]),
		list.Min([#MAX_TASK_SIZE[1], math.Ceil((_bounds[1][1]-_bounds[1][0])/dst_resolution[1])]),
		1,
	]

	"@type": "build_subchunkable_apply_flow"
	op: {
		"@type": "WarpOperation"
		mode:    "field"
		crop_pad: [256, 256, 0]
	}
	dst_resolution: _
	processing_chunk_sizes: [max_chunk_size]
	processing_crop_pads: [[0, 0, 0]]
	skip_intermediaries:    true
	expand_bbox_processing: true
	bbox: {
		"@type": "BBox3D.from_coords"
		start_coord: [_bounds[0][0], _bounds[1][0], _bounds[2][0]]
		end_coord: [_bounds[0][1], _bounds[1][1], _bounds[2][1]]
	}
	op_kwargs: {
		src: {
			"@type": "build_cv_layer"
			path:    #AFFINE_INV_FIELD_PATH
		}
		field: {
			"@type": "build_cv_layer"
			path:    #COARSE_WO_AFFINE_FIELD_PATH
			// data_resolution: [6144, 6144, 45]
			// interpolation_mode: "field"
		}
	}
	dst: {
		"@type":             "build_cv_layer"
		path:                #COARSE_INV_FIELD_PATH
		info_reference_path: op_kwargs.src.path
		on_info_exists:      "overwrite"
	}
}


#INVERT_FIELD_TEMPLATE: {
	let max_chunk_size = [
		list.Min([#MAX_TASK_SIZE[0], math.Ceil((#ROI_BOUNDS[0][1]-#ROI_BOUNDS[0][0])/dst_resolution[0])]),
		list.Min([#MAX_TASK_SIZE[1], math.Ceil((#ROI_BOUNDS[1][1]-#ROI_BOUNDS[1][0])/dst_resolution[1])]),
		1,
	]

	"@type": "build_subchunkable_apply_flow"
	fn: {"@type": "invert_field", "@mode": "partial"}
	dst_resolution: _
	processing_chunk_sizes: [max_chunk_size]
	processing_crop_pads: [[0, 0, 0]]
	skip_intermediaries:    true
	expand_bbox_processing: true
	bbox: {
		"@type": "BBox3D.from_coords"
		start_coord: [#ROI_BOUNDS[0][0], #ROI_BOUNDS[1][0], #ROI_BOUNDS[2][0]]
		end_coord: [#ROI_BOUNDS[0][1], #ROI_BOUNDS[1][1], #ROI_BOUNDS[2][1]]
	}
	op_kwargs: {
		src: {
			"@type": "build_cv_layer"
			path:    #COARSE_INV_FIELD_PATH
		}
	}
	dst: {
		"@type":             "build_cv_layer"
		path:                #COARSE_FIELD_PATH
		info_reference_path: op_kwargs.src.path
		info_add_scales:     [[6144, 6144, 45]]
		info_add_scales_mode: "replace"
		on_info_exists:      "overwrite"
	}
}

#WARP_ENC_TEMPLATE: {
	_bounds: _ | *#ROI_BOUNDS
	let max_chunk_size = [
		list.Min([#MAX_TASK_SIZE[0], math.Ceil((_bounds[0][1]-_bounds[0][0])/dst_resolution[0])]),
		list.Min([#MAX_TASK_SIZE[1], math.Ceil((_bounds[1][1]-_bounds[1][0])/dst_resolution[1])]),
		1,
	]

	"@type": "build_subchunkable_apply_flow"
	op: {
		"@type": "WarpOperation"
		mode:    "image"
		crop_pad: [256, 256, 0]
	}
	dst_resolution: _
	processing_chunk_sizes: [max_chunk_size]
	processing_crop_pads: [[0, 0, 0]]
	skip_intermediaries:    true
	expand_bbox_processing: true
	bbox: {
		"@type": "BBox3D.from_coords"
		start_coord: [_bounds[0][0], _bounds[1][0], _bounds[2][0]]
		end_coord: [_bounds[0][1], _bounds[1][1], _bounds[2][1]]
	}
	op_kwargs: {
		src: {
			"@type": "build_cv_layer"
			path:    #UNALIGNED_ENC_PATH
		}
		field: {
			"@type": "build_cv_layer"
			path:    #COARSE_INV_FIELD_PATH
			data_resolution: [6144, 6144, 45]
			interpolation_mode: "field"
		}
	}
	dst: {
		"@type":             "build_cv_layer"
		path:                #COARSE_ENC_PATH
		info_reference_path: op_kwargs.src.path
		info_add_scales:     [[6144, 6144, 45], [12288, 12288, 45]]
		info_add_scales_mode: "replace"
		on_info_exists:      "overwrite"
	}
}

// #WARP_TISSUE_TEMPLATE: {
// 	_bounds: _ | *#ROI_BOUNDS
// 	let max_chunk_size = [
// 		list.Min([#MAX_TASK_SIZE[0], math.Ceil((_bounds[0][1]-_bounds[0][0])/dst_resolution[0])]),
// 		list.Min([#MAX_TASK_SIZE[1], math.Ceil((_bounds[1][1]-_bounds[1][0])/dst_resolution[1])]),
// 		1,
// 	]

// 	"@type": "build_subchunkable_apply_flow"
// 	op: {
// 		"@type": "WarpOperation"
// 		mode:    "image"
// 		crop_pad: [256, 256, 0]
// 	}
// 	dst_resolution: _
// 	processing_chunk_sizes: [max_chunk_size]
// 	processing_crop_pads: [[0, 0, 0]]
// 	skip_intermediaries:    true
// 	expand_bbox_processing: true
// 	bbox: {
// 		"@type": "BBox3D.from_coords"
// 		start_coord: [_bounds[0][0], _bounds[1][0], _bounds[2][0]]
// 		end_coord: [_bounds[0][1], _bounds[1][1], _bounds[2][1]]
// 	}
// 	op_kwargs: {
// 		src: {
// 			"@type": "build_cv_layer"
// 			path:    #UNALIGNED_ENC_PATH
// 		}
// 		field: {
// 			"@type": "build_cv_layer"
// 			path:    #COARSE_INV_FIELD_PATH
// 			data_resolution: [6144, 6144, 45]
// 			interpolation_mode: "field"
// 		}
// 	}
// 	dst: {
// 		"@type":             "build_cv_layer"
// 		path:                #COARSE_TISSUE_PATH
// 		info_reference_path: op_kwargs.src.path
// 		info_add_scales:     [[6144, 6144, 45], [12288, 12288, 45]]
// 		info_add_scales_mode: "replace"
// 		on_info_exists:      "overwrite"
// 	}
// }
