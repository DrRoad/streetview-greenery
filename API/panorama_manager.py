
import os
import json
import numpy as np
from tqdm import tqdm

from models.deeplab import DeepLabModel
from abc import ABC
from greenery.segment_perc import VegetationPercentage


class BasePanoramaManager(ABC):
    " Object for using the Amsterdam data API"

    def __init__(self, seg_model=DeepLabModel, seg_kwargs={},
                 green_model=VegetationPercentage, green_kwargs={}):
        self.meta_data = []
        self.panoramas = []
        self.data_dir = "data.default"
        self.seg_model = seg_model(**seg_kwargs)
        self.green_model = green_model(**green_kwargs)

    def get(self, **request_kwargs):
        data_dir = self.data_dir
        params = self._request_params(**request_kwargs)
        meta_file = self._meta_request_file(params)
        meta_fp = os.path.join(data_dir, meta_file)

        if os.path.exists(meta_fp):
            with open(meta_fp, "r") as f:
                self.meta_data = json.load(f)
        else:
            self.meta_data = self.request_meta(params)
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)
            with open(meta_fp, "w") as f:
                json.dump(self.meta_data, f, indent=2)

        print(f"List contains {len(self.meta_data)} pictures. ")

    def load(self, n_sample=None):
        n_panorama = len(self.meta_data)
        np.random.seed(1283742)
        if n_sample is None:
            load_ids = np.arange(n_panorama)
        else:
            load_ids = np.random.choice(n_panorama, n_sample, replace=False)
        dest_dir = os.path.join(self.data_dir, "pics")
        os.makedirs(dest_dir, exist_ok=True)

        self.meta_data = [self.meta_data[i] for i in load_ids]
        print("Loading panoramas..")
        for meta in tqdm(self.meta_data):
            self.panoramas.append(self.new_panorama(meta_data=meta))

    def seg_analysis(self):
        print("Doing segmentation analysis..")
        for panorama in tqdm(self.panoramas):
            panorama.seg_analysis(seg_model=self.seg_model)

    def green_analysis(self):
        green_dict = {
            'green': [],
            'lat': [],
            'long': [],
        }
        print("Doing greenery analysis..")
        for panorama in tqdm(self.panoramas):
            green_frac = panorama.green_analysis(seg_model=self.seg_model,
                                                 green_model=self.green_model)
            green_dict["green"].append(green_frac)
            green_dict["lat"].append(panorama.latitude)
            green_dict["long"].append(panorama.longitude)
        return green_dict

