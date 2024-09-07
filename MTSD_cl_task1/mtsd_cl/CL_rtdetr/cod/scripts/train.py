import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import argparse

os.makedirs("./outputs", exist_ok=True)

import src.misc.dist as dist
from src.core import YAMLConfig
from src.solver import TASKS
from src.data import ABR

import wandb
import torch
import numpy as np


def set_seed_and_config():
    np.random.seed(42)
    torch.manual_seed(42)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = False


def main(
    args,
) -> None:
    
    abr = ABR(
        images_dir = args.images_dir,
        ann_file = args.ann_file,
        buffered_images_dir = args.buffered_images_dir,
        data_ratio = args.data_ratio
    )
    abr.save_buffer_image_and_annotations()
    
    set_seed_and_config()
    dist.init_distributed()

    assert not all(
        [args.tuning, args.resume]
    ), "Only support from_scratch or resume or tuning at one time"

    cfg = YAMLConfig(
        args.config, resume=args.resume, use_amp=args.amp, tuning=args.tuning
    )

    solver = TASKS[cfg.yaml_cfg["task"]](cfg)

    if args.test_only:
        solver.val()
    else:
        solver.fit()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        "-c",
        default="configs/rtdetr/rtdetr_r50vd_coco.yml",
        type=str,
    )
    parser.add_argument(
        "--resume",
        "-r",
        type=str,
    )
    parser.add_argument(
        "--tuning",
        "-t",
        default="",
        type=str,
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--amp",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--images_dir",
        default="./mapillary-traffic-sign-dataset/mtsd_fully_annotated_train_images/images"
    )
    parser.add_argument(
        "--ann_file",
        default="./mtsd-preprocessing/train_output_file_coco.json"
    )
    parser.add_argument(
        "--buffered_images_dir",
        default="./buffer"
    )
    parser.add_argument(
        "--data_ratio",
        default="15071"
    )

    args = parser.parse_args()
    main(args)