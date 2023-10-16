import json
import pandas as pd
from datetime import datetime
from nfp_assistant import NFPAssistant
from shapely.geometry import Polygon
from show import PltFunc
from util.packing_util import get_inner_fit_rectangle
from util.polygon_util import (
    check_bound,
    check_right,
    check_top,
    poly_to_arr,
    scale_polygon,
    slide_poly,
    slide_to_point,
)


class BottomLeftFill(object):
    def __init__(self, width, original_polygons, nfp_assistant, **kw):
        self.choose_nfp = False
        self.width = width
        self.length = 150000  # 代表长度
        self.contain_length = 2000
        self.polygons = original_polygons
        self.nfp_assistant = nfp_assistant
        self.vertical = False
        if "vertical" in kw:
            self.vertical = kw["vertical"]

        print("Total Num:", len(original_polygons))
        self.placeFirstPoly()
        for i in range(1, len(self.polygons)):
            print(f"##### Place the {i + 1}th shape #####")
            self.placePoly(i)
        self.getLength()

    def placeFirstPoly(self):
        poly = self.polygons[0]
        left_index, bottom_index, _, _ = check_bound(poly)  # 获得边界
        slide_poly(poly, -poly[left_index][0], -poly[bottom_index][1])  # 平移到左下角

    def placePoly(self, index):
        adjoin = self.polygons[index]
        # 是否垂直
        if self.vertical == True:
            ifr = get_inner_fit_rectangle(self.polygons[index], self.width, self.length)
        else:
            ifr = get_inner_fit_rectangle(self.polygons[index], self.length, self.width)
        differ_region = Polygon(ifr)

        for main_index in range(0, index):
            main = self.polygons[main_index]
            nfp = self.nfp_assistant.getDirectNFP(main, adjoin)
            nfp_poly = Polygon(nfp)
            try:
                differ_region = differ_region.difference(nfp_poly)
            except:
                print("NFP failure, areas of polygons are:")
                self.showAll()
                for poly in main, adjoin:
                    print(Polygon(poly).area)
                self.showPolys([main] + [adjoin] + [nfp])
                print("NFP loaded from: ", self.nfp_assistant.history_path)

        differ = poly_to_arr(differ_region)
        differ_index = self.getBottomLeft(differ)
        refer_pt_index = check_top(adjoin)
        slide_to_point(
            self.polygons[index], adjoin[refer_pt_index], differ[differ_index]
        )

    def getBottomLeft(self, poly):
        """
        获得左底部点，优先左侧，有多个左侧选择下方
        """
        bl = []  # bottom left的全部点
        _min = 999999
        # 选择最左侧的点
        for i, pt in enumerate(poly):
            pt_object = {"index": i, "x": pt[0], "y": pt[1]}
            if self.vertical == True:
                target = pt[1]
            else:
                target = pt[0]
            if target < _min:
                _min = target
                bl = [pt_object]
            elif target == _min:
                bl.append(pt_object)
        if len(bl) == 1:
            return bl[0]["index"]
        else:
            if self.vertical == True:
                target = "x"
            else:
                target = "y"
            _min = bl[0][target]
            one_pt = bl[0]
            for pt_index in range(1, len(bl)):
                if bl[pt_index][target] < _min:
                    one_pt = bl[pt_index]
                    _min = one_pt["y"]
            return one_pt["index"]

    def showAll(self):
        # for i in range(0,2):
        for i in range(0, len(self.polygons)):
            PltFunc.addPolygon(self.polygons[i])
        length = max(self.width, self.contain_length)
        # PltFunc.addLine([[self.width,0],[self.width,self.contain_height]],color="blue")
        PltFunc.showPlt(
            width=max(length, self.width), height=max(length, self.width), minus=100
        )

    def showPolys(self, polys):
        for i in range(0, len(polys) - 1):
            PltFunc.addPolygon(polys[i])
        PltFunc.addPolygonColor(polys[len(polys) - 1])
        length = max(self.width, self.contain_length)
        PltFunc.showPlt(
            width=max(length, self.width), height=max(length, self.width), minus=200
        )

    def getLength(self):
        _max = 0
        for i in range(0, len(self.polygons)):
            if self.vertical == True:
                extreme_index = check_top(self.polygons[i])
                extreme = self.polygons[i][extreme_index][1]
            else:
                extreme_index = check_right(self.polygons[i])
                extreme = self.polygons[i][extreme_index][0]
            if extreme > _max:
                _max = extreme
        self.contain_length = _max
        # PltFunc.addLine([[0,self.contain_length],[self.width,self.contain_length]],color="blue")
        return _max


if __name__ == "__main__":
    df = pd.read_csv("data/shirts_yuanhao.csv")
    polygons = [json.loads(row["polygon"]) for _, row in df.iterrows()]
    scaled_polygons = [scale_polygon(polygon, 10) for polygon in polygons]
    nfp_assistant = NFPAssistant(
        polys=scaled_polygons, store_nfp=True, get_all_nfp=True, load_history=False
    )

    start_time = datetime.now()
    bfl = BottomLeftFill(
        width=1000,
        length=950,
        original_polygons=scaled_polygons,
        vertical=False,
        nfp_assistant=nfp_assistant,
    )
    end_time = datetime.now()
    print("total time: ", end_time - start_time)
    bfl.showAll()