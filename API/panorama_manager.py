'''
Manager of a set of panoramas.
'''
import os
import json
import numpy as np
from tqdm import tqdm

from models import DeepLabModel
from abc import ABC
from greenery import VegetationPercentage
from urllib.error import HTTPError


class BasePanoramaManager(ABC):
    " Base class for managing a data set of panoramas. "

    def __init__(self, seg_model=DeepLabModel, seg_kwargs={},
                 green_model=VegetationPercentage, green_kwargs={},
                 data_id="unknown"):
        self.meta_data = []
        self.panoramas = []
        self.data_dir = "data.default"
        self.seg_model = seg_model(**seg_kwargs)
        self.green_model = green_model(**green_kwargs)
        self.id = data_id

    def get(self, **request_kwargs):
        " Get meta data of the requested pictures. "
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

    def load(self, n_sample=None, load_ids=None):
        """ Download/read pictures.

        Arguments
        ---------
        n_sample: int
            Sample that number of pictures. If n_sample is None,
            download/load all panorama's.
        """
        n_panorama = len(self.meta_data)
        # Set the seed, so that we will get the same samples each time.
        if load_ids is None:
            if n_sample is None:
                load_ids = np.arange(n_panorama)
            else:
                np.random.seed(1283742)
                load_ids = np.random.choice(
                    n_panorama, n_sample, replace=False)

        dest_dir = os.path.join(self.data_dir, "pics")
        os.makedirs(dest_dir, exist_ok=True)

        self.meta_data = [self.meta_data[i] for i in load_ids]
        print("Loading panoramas..")
        for meta in tqdm(self.meta_data):
            try:
                self.panoramas.append(self.new_panorama(meta_data=meta))
            except HTTPError:
                print(f"Error retrieving panorama data, skipping.")
                print(meta)

    def seg_analysis(self, **kwargs):
        " Do segmentation analysis. "
        print("Doing segmentation analysis..")
        for panorama in tqdm(self.panoramas):
            panorama.seg_analysis(seg_model=self.seg_model, **kwargs)

    def green_analysis(self):
        """
        Do greenery analysis.

        Returns
        -------
        dict:
            Dictionary that contains greenery points at (lat,long).
        """
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
