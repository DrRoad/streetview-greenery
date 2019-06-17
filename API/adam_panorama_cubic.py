
import os
from os.path import splitext
import urllib.request
from API.base_panorama import BasePanorama
import numpy as np
from models.deeplab import plot_segmentation
from tqdm._tqdm import tqdm
from API.idgen import get_green_key


# def _meta_fp(panorama_fp):
#     base_fp = splitext(panorama_fp)[0]
#     return base_fp+"_meta"+".json"


def _corrected_fractions(seg_map, names):
    nclass = 200
    ny = seg_map.shape[0]
    nx = seg_map.shape[1]
    seg_frac_dict = {}
    seg_frac = np.zeros(nclass)
    tot_frac = 0
    for iy in range(ny):
        dy = 2*iy/ny-1
        for ix in range(nx):
            dx = 2*ix/nx-1
            fac = (dx**2+dy**2+1)**-1.5
            seg_frac[seg_map[iy, ix]] += fac
            tot_frac += fac

    print(tot_frac)
    for i in range(nclass):
        if seg_frac[i] > 0:
            seg_frac_dict[names[i]] = seg_frac[i]/tot_frac
    return seg_frac_dict


class AdamPanoramaCubic(BasePanorama):
    " Object for using the Amsterdam data API with equirectengular data. "
    def __init__(self, meta_data, data_src="data.amsterdam", data_dir=None):
        self.sides = {
            "front": "f",
            "back": "b",
#             "up": "u",
            "left": "l",
            "right": "r",
        }

        if data_dir is None:
            data_dir = os.path.join(data_src, "pics")
        super(AdamPanoramaCubic, self).__init__(
            meta_data=meta_data,
            data_dir=data_dir,
            data_src=data_src,
        )

    def parse(self, meta_data):
        " Get some universally used data. "
        self.meta_data = meta_data
        self.latitude = meta_data["geometry"]["coordinates"][1]
        self.longitude = meta_data["geometry"]["coordinates"][0]
        self.id = meta_data["pano_id"]

    def fp_from_meta(self, meta_data):
        " Generate the meta and picture filenames. "

        self.pano_url = []
        self.panorama_dir = self.data_dir
        self.panorama_fp = {}
        self.meta_fp = os.path.join(self.data_dir, "meta_data.json")
        if not os.path.exists(self.panorama_dir):
            os.makedirs(self.panorama_dir)
        for side in self.sides:
            abrev = self.sides[side]
            self.pano_url.append(meta_data["cubic_img_baseurl"] +
                                 f"1/{abrev}/0/0.jpg")
            self.panorama_fp[side] = os.path.join(
                self.panorama_dir, side+".jpg")

            if not os.path.exists(self.panorama_fp[side]):
                urllib.request.urlretrieve(self.pano_url[-1],
                                           self.panorama_fp[side])

    def seg_analysis(self, seg_model, show=False, recalc=False):
        model_id = seg_model.id()
        self.segment_fp = os.path.join(self.data_dir,
                                       f"segments_cubic_{model_id}.json")

        self.load_segmentation(self.segment_fp)
        if len(self.all_seg_res) < 1:
            self.all_seg_res = self.seg_run(seg_model, show=show)
            self.save_segmentation(self.segment_fp)
        elif show:
            self.show()

    def green_analysis(self, seg_model, green_model):
        self.green_fp = os.path.join(self.data_dir, "greenery.json")
        green_id = green_model.id()
        seg_id = seg_model.id()
        key = get_green_key(AdamPanoramaCubic, seg_id, green_id)
        self.load_greenery(self.green_fp)
        if key not in self.all_green_res:
            if len(self.all_seg_res) < 1:
                self.seg_analysis(seg_model)

            seg_frac = {}
            n_pano = len(self.all_seg_res)
            for name in self.all_seg_res:
                seg_res = self.all_seg_res[name]
                seg_map = np.array(seg_res['seg_map'])
                names = np.array(seg_res['color_map'][0])
                new_frac = green_model.test_seg_map2(seg_map, names)

#                 green_val = green_model.test(new_frac)
#                 greenery += green_model.test_seg_map(seg_map, names)/n_pano
#                 print(green_model.test_seg_map(seg_map, names))
#                 print(green_model.test_seg_map2(seg_map, names))
#                 print(green_val, other_green_val)
#                 import sys
#                 sys.exit()

                for class_name in new_frac:
                    if class_name in seg_frac:
                        seg_frac[class_name] += new_frac[class_name]/n_pano
                    else:
                        seg_frac[class_name] = new_frac[class_name]/n_pano
            self.all_green_res[key] = seg_frac
            self.save_greenery(self.green_fp)
        return green_model.test(self.all_green_res[key])

    def seg_run(self, model, show=False):
        " Do segmentation analysis on the picture. "

        seg_res = {}
        for side in self.panorama_fp:
            pano_fp = self.panorama_fp[side]
            new_seg_res = model.run(pano_fp)
            seg_res[side] = new_seg_res

        if show:
            self.show()

        return seg_res

    def show(self):
        for side in self.all_seg_res:
            pano_fp = self.panorama_fp[side]
            seg_res = self.all_seg_res[side]
            seg_map = np.array(seg_res['seg_map'])
            color_map = seg_res["color_map"]
            names = np.array(color_map[0])

            plot_labels = {}
            fractions = _corrected_fractions(seg_map, names)
            for name in fractions:
                if fractions[name] < 0.001:
                    continue
                name_id = np.where(names == name)[0][0]
                plot_labels[name_id] = fractions[name]
            plot_segmentation(pano_fp, seg_map, color_map,
                              plot_labels=plot_labels)
