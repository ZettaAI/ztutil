#IMG_PATH: "gs://dacey-human-retina-001-alignment-temp/rigid/img"
#IMG_RES: [5, 5, 50]
#IMG_SIZE: [65536, 65536, 3030]

#Z_OFFSETS: _ | *[-2, -1]

// FOLDERS
#FOLDER:        "gs://dacey-human-retina-001-alignment-temp"
#PROJECT:       "test-240124"
#BASE_FOLDER:   "gs://dacey-human-retina-001-alignment-temp/aced/\(#PROJECT)"
#TMP_FOLDER:    "gs://tmp_2w/nico/aced"

// FINAL OUTPUT PATHS
// #IMG_ALIGNED_PATH:  "gs://dkronauer-ant-001-alignment-final/ppc"
// #IMG_MASK_PATH:     "gs://dkronauer-ant-001-alignment-final/ppc-img-mask"
// #AFF_MASK_PATH:     "gs://dkronauer-ant-001-alignment-final/ppc-aff-mask"

#TEST_SMALL: true
#TEST_LOCAL: false

#CLUSTER_NUM_WORKERS: 128
// #CLUSTER_NUM_WORKERS: 32

#RUN_OFFSET:                false
#RUN_RELAX_FLOW:            false
//#RUN_POST_ALIGN_FLOW:       false
//#RUN_POST_ALIGN_WARP:       false
#RUN_POST_ALIGN_IMG_MASK:   false
#RUN_POST_ALIGN_AFF_MASK:   false


if #TEST_SMALL == true {
    // #START_COORD_XY: [11*4096, 5*4096]
    // #END_COORD_XY: [18*4096, 10*4096]
    // #START_COORD_XY: [32*1024, 16*1024]
    // #END_COORD_XY: [72*1024, 40*1024]
    #IMG_WARP_OUTPUT_RES: [40, 40, #IMG_RES[2]]     // fast test output
    #RELAXATION_RESOLUTION: [320, 320, #IMG_RES[2]]
    #BLOCKS: [{_z_start: 750, _z_end: 800,   _fix:  "both"}]
    #RELAXATION_ITER: 9000
    // #RELAXATION_ITER: 1000
    #RELAXATION_RIG:  3.0
    #MISALIGNMENTS_PATH: "gs://dacey-human-retina-001-alignment-temp/pairwise/misd_manual"
    // set misalignment mask threshold separately for -1 and -2
    #MATCH_OFFSETS_FLOW: op_kwargs: misalignment_masks: "-1": read_procs: [{value: 127}, ...]
    #MATCH_OFFSETS_FLOW: op_kwargs: misalignment_masks: "-2": read_procs: [{value: 127}, ...]

    // set input resolution, but these really should be downsampled
    // misalignments
    #MATCH_OFFSETS_FLOW: op_kwargs: misalignment_masks: "-1": data_resolution: [320, 320, #IMG_RES[2]]
    #MATCH_OFFSETS_FLOW: op_kwargs: misalignment_masks: "-2": data_resolution: [320, 320, #IMG_RES[2]]

    #MATCH_OFFSETS_FLOW: op_kwargs: tissue_mask: data_resolution: [320, 320, #IMG_RES[2]]
    // fields
    #MATCH_OFFSETS_FLOW: op_kwargs: pairwise_fields: "-1": data_resolution: [320, 320, #IMG_RES[2]]
    #MATCH_OFFSETS_FLOW: op_kwargs: pairwise_fields: "-2": data_resolution: [320, 320, #IMG_RES[2]]
    #MATCH_OFFSETS_FLOW: op_kwargs: pairwise_fields_inv: "-1": data_resolution: [320, 320, #IMG_RES[2]]
    #MATCH_OFFSETS_FLOW: op_kwargs: pairwise_fields_inv: "-2": data_resolution: [320, 320, #IMG_RES[2]]
    #RELAX_FLOW: op_kwargs: pfields: "-1": data_resolution: [320, 320, #IMG_RES[2]]
    #RELAX_FLOW: op_kwargs: pfields: "-2": data_resolution: [320, 320, #IMG_RES[2]]
    // defect mask
    #DEFECTS_PATH: "gs://dacey-human-retina-001-alignment-temp/rigid/defect_mask_refine"
    #RELAX_FLOW: op_kwargs: rigidity_masks: data_resolution: [320, 320, #IMG_RES[2]]

    #COARSE_AFIELD_PATH: "gs://dacey-human-retina-001-alignment-temp/aced/afield_try_2560nm_iter18000_rig3.0_lr0.0001"
    #RELAX_FLOW: op_kwargs: first_section_fix_field: data_resolution: [2560, 2560, #IMG_RES[2]]
    #RELAX_FLOW: op_kwargs: last_section_fix_field: data_resolution: [2560, 2560, #IMG_RES[2]]
}


//// PARAMETERS
#RELAXATION_ITER: _ | *8000
#RELAXATION_LR:         1e-4
// #RELAXATION_RIG:        3.0
// #RELAXATION_RIG:        1.0
#RELAXATION_RIG:        _ | *0.5
#RELAXATION_RESOLUTION: _ | *[640, 640, #IMG_RES[2]]


// Be more conservative with the misalignment outputs, set lower to be more conservative
#MISALIGNMENTS_THRESHOLD: 64

// #IMG_WARP_OUTPUT_RES: [8, 8, #IMG_RES[2]]
// #IMG_WARP_DOWNSAMPLING: [2, 2, 1]  // warp from 4nm data
#RELAX_OUTCOME_CHUNK_SIZE: [32, 32, 1]

// OTHER VARIABLES
#DEBUG_SUFFIX: _ | *"z750_800"
#FOLDER:                    _ | *"\(#BASE_FOLDER)/pair"
#TMP_PATH:                  "\(#TMP_FOLDER)/\(#PROJECT)/\(#RELAXATION_SUFFIX)"
#FIELDS_PATH:               "\(#FOLDER)/pairwise/field/fwd"
#FIELDS_INV_PATH:           "\(#FOLDER)/pairwise/field/inv"
#MISALIGNMENTS_PATH:        _ | *"\(#FOLDER)/pairwise/misd_manual"
#TISSUE_MASK_PATH: "gs://dacey-human-retina-001-alignment-temp/rigid/tissue_mask"
#AFIELD_PATH:               "\(#FOLDER)/aced/afield\(#RELAXATION_SUFFIX)"
#IMG_ALIGNED_PATH:          _ | *"\(#FOLDER)/aced/img_aligned\(#RELAXATION_SUFFIX)"
#IMG_MASK_PATH:             _ | *"\(#FOLDER)/aced/img_mask\(#RELAXATION_SUFFIX)"
#AFF_MASK_PATH:             _ | *"\(#FOLDER)/aced/aff_mask\(#RELAXATION_SUFFIX)"
#MATCH_OFFSET_BASE:         "\(#FOLDER)/aced/match_offsets_\(#RELAXATION_RESOLUTION[0])nm"
#RELAXATION_SUFFIX: "_try_\(#RELAXATION_RESOLUTION[0])nm" +
                    "_iter\(#RELAXATION_ITER)" +
                    "_rig\(#RELAXATION_RIG)" +
                    "_lr\(#RELAXATION_LR)" +
                    "\(#DEBUG_SUFFIX)"

#COARSE_AFIELD_PATH: _



#BBOX_TMPL: {
    "@type":  "BBox3D.from_coords"
    _z_start: int
    _z_end:   int
    start_coord: [#START_COORD_XY[0], #START_COORD_XY[1], _z_start]
    end_coord: [#END_COORD_XY[0], #END_COORD_XY[1], _z_end]
    resolution: #IMG_RES
}
#START_COORD_XY: _ | *[0, 0]
#END_COORD_XY: _ | *[#IMG_SIZE[0], #IMG_SIZE[1]]
#BLOCKS: _ | *[
    {_z_start: 0,   _z_end: #IMG_SIZE[2]},
]

#MISALIGNMENTS_READ_PROCS: {
    
}

#MISALIGNMENTS_THRESHOLD: _ | *128
#MATCH_OFFSETS_FLOW: {
    "@type": "build_subchunkable_apply_flow"
    op: {
        "@type": "AcedMatchOffsetOp"
    }
    bbox: _
    processing_chunk_sizes: [[32, 32, bbox._z_end - bbox._z_start]]
    processing_crop_pads: [[32, 32, 0]]
    dst_resolution: #RELAXATION_RESOLUTION
    // level_intermediaries_dirs: ["~/.zutils/tmp"]
    skip_intermediaries: true
    op_kwargs: {
        max_dist: _ | *2
        tissue_mask: _ | *{
            "@type": "build_cv_layer"
            path:    #TISSUE_MASK_PATH
            data_resolution?: _
            interpolation_mode: "img"
        }
        misalignment_masks: {
            for offset in #Z_OFFSETS {
                "\(offset)": {
                    "@type": "build_cv_layer"
                    path:    "\(#MISALIGNMENTS_PATH)/z\(offset)"
                    read_procs: [
                        {
                            "@type": "compare"
                            "@mode": "partial"
                            mode:    ">="
                            value:   _ | *#MISALIGNMENTS_THRESHOLD
                        },
                        {
                            "@type": "filter_cc"
                            "@mode": "partial"
                            thr:     10
                            mode:    "keep_large"
                        },
                        {
                            // remove small islands of `false` (aligned pixels)
                            "@type": "kornia_closing"
                            "@mode": "partial"
                            width:   4
                        },
                        {
                            // grow misalignment mask by 1 pix
                            "@type": "kornia_dilation"
                            "@mode": "partial"
                            width:   3
                        },
                        {
                            "@type": "to_uint8"
                            "@mode": "partial"
                        },
                    ]
                    data_resolution?: _
                    interpolation_mode: "img"
                }
            }
        }
        pairwise_fields: {
            for offset in #Z_OFFSETS {
                "\(offset)": {
                    "@type": "build_cv_layer"
                    path:    "\(#FIELDS_PATH)/z\(offset)"
                    data_resolution?: _
                    interpolation_mode: "field"
                }
            }
        }
        pairwise_fields_inv: {
            for offset in #Z_OFFSETS {
                "\(offset)": {
                    "@type": "build_cv_layer"
                    path:    "\(#FIELDS_INV_PATH)/z\(offset)"
                    data_resolution?: _
                    interpolation_mode: "field"
                }
            }
        }
    }
    let match_offsets_path = "\(#MATCH_OFFSET_BASE)_\(bbox._z_start)_\(bbox._z_end)"
    dst: {
        "@type": "build_volumetric_layer_set"
        layers: {
            match_offsets: {
                "@type":             "build_cv_layer"
                path:                match_offsets_path
                info_reference_path: #IMG_PATH
                info_chunk_size:     #RELAX_OUTCOME_CHUNK_SIZE
                info_add_scales:     [dst_resolution]
                info_add_scales_mode: "replace"
                on_info_exists:      "overwrite"
                write_procs: [
                    {"@type": "to_uint8", "@mode": "partial"},
                ]
            }
            img_mask: {
                "@type":             "build_cv_layer"
                path:                "\(match_offsets_path)/img_mask"
                info_reference_path: #IMG_PATH
                info_chunk_size:     #RELAX_OUTCOME_CHUNK_SIZE
                info_add_scales:     [dst_resolution]
                info_add_scales_mode: "replace"
                on_info_exists:      "overwrite"
                write_procs: [
                    {"@type": "filter_cc", "@mode": "partial", thr: 3, mode: "keep_large"},
                    {"@type": "to_uint8", "@mode":  "partial"},
                ]
            }
            aff_mask: {
                "@type":             "build_cv_layer"
                path:                "\(match_offsets_path)/aff_mask"
                info_reference_path: #IMG_PATH
                info_chunk_size:     #RELAX_OUTCOME_CHUNK_SIZE
                info_add_scales:     [dst_resolution]
                info_add_scales_mode: "replace"
                on_info_exists:      "overwrite"
                write_procs: [
                    {"@type": "filter_cc", "@mode": "partial", thr: 3, mode: "keep_large"},
                    {"@type": "to_uint8", "@mode":  "partial"},
                ]
            }
            sector_length_before: {
                "@type":             "build_cv_layer"
                path:                "\(match_offsets_path)/sl_before"
                info_reference_path: #IMG_PATH
                info_chunk_size:     #RELAX_OUTCOME_CHUNK_SIZE
                info_add_scales:     [dst_resolution]
                info_add_scales_mode: "replace"
                on_info_exists:      "overwrite"
                write_procs: [
                    {"@type": "to_uint8", "@mode": "partial"},
                ]
            }
            sector_length_after: {
                "@type":             "build_cv_layer"
                path:                "\(match_offsets_path)/sl_after"
                info_reference_path: #IMG_PATH
                info_chunk_size:     #RELAX_OUTCOME_CHUNK_SIZE
                info_add_scales:     [dst_resolution]
                info_add_scales_mode: "replace"
                on_info_exists:      "overwrite"
                write_procs: [
                    {"@type": "to_uint8", "@mode": "partial"},
                ]
            }
        }
    }
}

#DEFECTS_PATH: _ | *""
#TISSUE_MASK_PATH: _ | *""
if #DEFECTS_PATH == "" {
    #RELAX_FLOW: op_kwargs: rigidity_masks: null
}
if #TISSUE_MASK_PATH == "" {
    #MATCH_OFFSETS_FLOW: op_kwargs: tissue_mask: {
        "@type": "build_constant_volumetric_layer"
        value: 1
    }
}
#RELAX_FLOW: {
    "@type": "build_subchunkable_apply_flow"
    op: {
        "@type": "AcedRelaxationOp"
    }
    expand_bbox_processing:    true
    dst_resolution: #RELAXATION_RESOLUTION
    bbox:           _
    processing_chunk_sizes: [[32, 32, bbox._z_end - bbox._z_start]]
    max_reduction_chunk_sizes: [32, 32, bbox._z_end - bbox._z_start]
    processing_crop_pads: [[24, 24, 0]]
    processing_blend_pads: [[16, 16, 0]]
    level_intermediaries_dirs: [#TMP_PATH]
    // skip_intermediaries: true
    op_kwargs: {
        max_dist: _ | *2
        fix:                     _
        num_iter:                #RELAXATION_ITER
        lr:                      #RELAXATION_LR
        rigidity_weight:         #RELAXATION_RIG
        rigidity_masks: _ | *{
            "@type": "build_cv_layer"
            path:    #DEFECTS_PATH
            read_procs: [
                {
                    "@type": "compare"
                    "@mode": "partial"
                    mode:    "=="
                    value:   0
                    // value:   1
                }
            ]
            data_resolution?: _
            interpolation_mode: "mask"
        }
        let match_offsets_path = "\(#MATCH_OFFSET_BASE)_\(bbox._z_start)_\(bbox._z_end)"
        match_offsets: {
            "@type": "build_cv_layer"
            path:    match_offsets_path
            //info_reference_path: #IMG_PATH
            on_info_exists: "overwrite"
        }
        pfields: {
            for offset in #Z_OFFSETS {
                "\(offset)": {
                    "@type": "build_cv_layer"
                    path:    "\(#FIELDS_PATH)/z\(offset)"
                    data_resolution?: _
                    interpolation_mode: "field"
                }
            }
        }
        first_section_fix_field: {
            "@type": "build_cv_layer"
            path:    #COARSE_AFIELD_PATH
            data_resolution?: _
            interpolation_mode: "field"
        }
        last_section_fix_field: {
            "@type": "build_cv_layer"
            path:    #COARSE_AFIELD_PATH
            data_resolution?: _
            interpolation_mode: "field"
        }
    }
    dst: {
        "@type":             "build_cv_layer"
        path:                #AFIELD_PATH
        info_reference_path: #IMG_PATH
        info_field_overrides: {
            num_channels: 2
            data_type:    "float32"
        }
        info_add_scales: [#RELAXATION_RESOLUTION]
        info_add_scales_mode: "replace"
        info_chunk_size: #RELAX_OUTCOME_CHUNK_SIZE
        on_info_exists:  "overwrite"
    }
}


#IMG_WARP_OUTPUT_RES:   _ | *[40, 40, #IMG_RES[2]]
#IMG_WARP_DOWNSAMPLING: _ | *[1, 1, 1]
#RUN_POST_ALIGN_WARP:     _ | *true
#RUN_POST_ALIGN_IMG_MASK: _ | *true
#RUN_POST_ALIGN_AFF_MASK: _ | *true
#POST_ALIGN_FLOW: {
    _bbox:   _
    "@type": "mazepa.concurrent_flow"
    let match_offsets_path = "\(#MATCH_OFFSET_BASE)_\(_bbox._z_start)_\(_bbox._z_end)"
    _dummy: match_offsets_path
    stages: [
        if #RUN_POST_ALIGN_WARP {
            #WARP_FLOW_TMPL & {
                bbox: _bbox
                op: mode: "img"
                op: downsampling_factor: #IMG_WARP_DOWNSAMPLING
                op_kwargs: src: path:              #IMG_PATH
                op_kwargs: field: path:            #AFIELD_PATH
                op_kwargs: field: data_resolution: #RELAXATION_RESOLUTION
                dst: path: #IMG_ALIGNED_PATH
                dst: info_add_scales: [#IMG_WARP_OUTPUT_RES]
                dst: info_add_scales_mode: "replace"
                dst_resolution: #IMG_WARP_OUTPUT_RES
            }
        }

        if #RUN_POST_ALIGN_IMG_MASK {
            #WARP_FLOW_TMPL & {
                op: mode: "mask"
                op_kwargs: {
                    src: path:              "\(match_offsets_path)/img_mask"
                    field: data_resolution: #RELAXATION_RESOLUTION
                    field: path:            #AFIELD_PATH
                }
                dst: path: #IMG_MASK_PATH
                dst_resolution: [640, 640, #IMG_RES[2]]
                dst: info_add_scales: [dst_resolution]
                dst: info_add_scales_mode: "replace"
                bbox: _bbox
            }
        }

        if #RUN_POST_ALIGN_AFF_MASK {
            #WARP_FLOW_TMPL & {
                op: mode: "mask"
                bbox: _bbox
                op_kwargs: {
                    src: path:              "\(match_offsets_path)/aff_mask"
                    field: data_resolution: #RELAXATION_RESOLUTION
                    field: path:            #AFIELD_PATH
                }
                dst: path: #AFF_MASK_PATH
                dst_resolution: [640, 640, #IMG_RES[2]]
                dst: info_add_scales: [dst_resolution]
                dst: info_add_scales_mode: "replace"
            }
        }
    ]
}

#WARP_FLOW_TMPL: {
    "@type": "build_subchunkable_apply_flow"
    op: {
        "@type": "WarpOperation"
        mode:    _
        downsampling_factor?: _
    }
    processing_chunk_sizes: [[1024 * 8, 1024 * 8, 1], [1024 * 2, 1024 * 2, 1]]
    processing_crop_pads: [[0, 0, 0], [256, 256, 0]]
    skip_intermediaries: true
    // level_intermediaries_dirs: [#TMP_PATH, "~/.zutils/tmp"]
    //chunk_size: [512, 512, 1]
    bbox:           _
    dst_resolution: _ | *[40, 40, #IMG_RES[2]]
    op_kwargs: {
        src: {
            "@type":      "build_cv_layer"
            path:         _
            read_procs?:  _
            index_procs?: _ | *[]
        }
        field: {
            "@type":            "build_cv_layer"
            path:               _
            data_resolution:    _ | *null
            interpolation_mode: "field"
        }
    }
    dst: {
        "@type":             "build_cv_layer"
        path:                _
        info_reference_path: #IMG_PATH
        info_add_scales?: _
        info_add_scales_mode?: _
        on_info_exists:      "overwrite"
        write_procs?:        _
        index_procs?:        _ | *[]
    }
}

#TEST_SMALL: _ | *false
#TEST_LOCAL: _ | *false
#RUN_OFFSET:             _ | *true
#RUN_RELAX_FLOW:         _ | *true
#RUN_POST_ALIGN_FLOW:    _ | *true
#RUN_INFERENCE: {
    "@type":      "mazepa.execute_on_gcp_with_sqs"
    worker_cluster_region:  "us-east1"
    worker_cluster_project: "dacey-human-retina-001"
    worker_cluster_name:    "zutils"
    worker_image:           "us-east1-docker.pkg.dev/zetta-research/zutils/zetta_utils:nico_py3.9_20240130"
    worker_resources: {
        "nvidia.com/gpu"?: _
    }
    worker_resource_requests: {
        memory: "21000Mi"       // sized for n1-highmem-4
    }
    worker_replicas:     #CLUSTER_NUM_WORKERS
    local_test:          #TEST_LOCAL
    if #TEST_LOCAL == true {
        debug: true
    }

    target: {
        "@type": "mazepa.concurrent_flow"
        stages: [
            for block in #BLOCKS {
                let bbox = #BBOX_TMPL & {_z_start: block._z_start, _z_end: block._z_end}
                "@type": "mazepa.sequential_flow"
                stages: [
                    if #RUN_OFFSET {
                        #MATCH_OFFSETS_FLOW & {'bbox': bbox},
                    }
                    if #RUN_RELAX_FLOW {
                        #RELAX_FLOW & {'bbox': bbox, op_kwargs: fix: block._fix},
                    }
                    if #RUN_POST_ALIGN_FLOW {
                        #POST_ALIGN_FLOW & {_bbox: bbox},
                    }
                ]
            },
        ]
    }
}
#RUN_INFERENCE
if #RUN_RELAX_FLOW | #RUN_POST_ALIGN_FLOW {
    #RUN_INFERENCE: worker_resources: "nvidia.com/gpu": "1"
}