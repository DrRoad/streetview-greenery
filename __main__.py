from API import PanoramaAmsterdam
from models import DeepLabModel
from greenery.segment_perc import VegetationPercentage, plot_greenery


def main():
    panoramas = PanoramaAmsterdam()
    cc = [52.299584, 4.971973]
    radius = 200  # meters
    panoramas.get(center=cc, radius=radius)
    panoramas.download(stride=1)
    panoramas.seg_analysis(model=DeepLabModel)
#     panoramas.print_ids()
#     panoramas.show(model=DeepLabModel)
    green_res = panoramas.greenery_analysis(model=DeepLabModel, greenery=VegetationPercentage)
    panoramas.save()
    plot_greenery(green_res)
#     print(green_res)


def test():
    green_res = {
        'green': [0.3, 0.4, 0.5],
        'lat': [1.0, 1.5, 3.0],
        'long': [-2.4, 3.2, -4.0],
    }
    plot_greenery(green_res)


if __name__ == "__main__":
    main()
#     test()
