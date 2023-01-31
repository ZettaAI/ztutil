		//#SRC_PATH: "gs://zfish_unaligned/precoarse_x0/raw_masked"
#SRC_PATH: "gs://zetta_jlichtman_zebrafish_001_alignment_temp/affine/v3_phase2/mip2_img"

//#DST_PATH: "gs://zfish_unaligned/coarse_x0/base_enc_x1"
#DST_PATH: "gs://zfish_unaligned/precoarse_x0/test_x0/encodings_x2"

//#MODEL_PATH: "gs://sergiy_exp/training_artifacts/base_encodings/tmp_gamma_low0.25_high4.0_prob1.0_tile_0.1_0.4_lr0.0003_x11/last.ckpt.static-1.12.1+cu102-model.jit"
#MODEL_PATH: "gs://sergiy_exp/training_artifacts/base_encodings/gen_x3_gamma_low0.25_high4.0_prob1.0_tile_0.1_0.4_lr0.0002_x0_try_x3/last.ckpt.static-1.12.1+cu102-model.jit"
///#MODEL_PATH: "gs://sergiy_exp/training_artifacts/base_encodings/tmp_gamma_low0.25_high4.0_prob1.0_tile_0.1_0.4_lr0.0003_x11/checkpoints/epoch=11-step=4666.ckpt.static-1.12.1+cu102-model.jit"

#CHUNK_SIZE: [2048, 2048, 1]

#DST_INFO_CHUNK_SIZE: [1024, 1024, 1]

#BBOX: {
	"@type": "BBox3D.from_coords"
	start_coord: [0, 0, 45]
	end_coord: [1024, 1024, 55]
	resolution: [512, 512, 30]
}

"@type":         "mazepa.execute_on_gcp_with_sqs"
worker_image:    "us.gcr.io/zetta-research/zetta_utils:sergiy_all_p39_x39"
worker_replicas: 10
worker_resources: {
	"nvidia.com/gpu": "1"
}

local_test: true

target: {
	"@type": "build_chunked_apply_flow"
	operation: {
		"@type": "VolumetricCallableOperation"
		fn: {
			"@type":    "BaseEncoder"
			model_path: #MODEL_PATH
		}
		crop_pad: [64, 64, 0]
	}
	chunker: {
		"@type":      "VolumetricIndexChunker"
		"chunk_size": #CHUNK_SIZE
	}
	src: {
		"@type": "build_cv_layer"
		path:    #SRC_PATH
	}
	dst: {
		"@type":             "build_cv_layer"
		path:                #DST_PATH
		info_reference_path: #SRC_PATH
		info_field_overrides: {
			data_type: "int8"
		}
		info_chunk_size: #DST_INFO_CHUNK_SIZE
		on_info_exists:  "overwrite"
	}
	idx: {
		"@type": "VolumetricIndex"
		bbox:    #BBOX
		resolution: [32, 32, 30]
	}
}
