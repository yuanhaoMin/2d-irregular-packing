import copy
import csv
import json
import pandas as pd
from nfp import NFP
from shapely.geometry import Polygon
from util.array_util import delete_redundancy, get_index_multi
from util.polygon_util import get_point, get_slide


class NFPAssistant(object):
    def __init__(self, polys, load_history):
        self.polys = delete_redundancy(copy.deepcopy(polys))
        self.area_list, self.first_vec_list, self.centroid_list = [], [], []  # 作为参考
        for poly in self.polys:
            P = Polygon(poly)
            self.centroid_list.append(get_point(P.centroid))
            self.area_list.append(int(P.area))
            self.first_vec_list.append(
                [poly[1][0] - poly[0][0], poly[1][1] - poly[0][1]]
            )
        self.nfp_list = [[0] * len(self.polys) for i in range(len(self.polys))]

        if load_history:
            self.loadHistory()
        else:
            self.getAllNFP()
            self.storeNFP()

    def loadHistory(self):
        path = "history/nfp.csv"
        df = pd.read_csv(path, header=None)
        for index in range(df.shape[0]):
            i = self.getPolyIndex(json.loads(df[0][index]))
            j = self.getPolyIndex(json.loads(df[1][index]))
            if i >= 0 and j >= 0:
                self.nfp_list[i][j] = json.loads(df[2][index])

    # 获得一个形状的index
    def getPolyIndex(self, target):
        area = int(Polygon(target).area)
        first_vec = [target[1][0] - target[0][0], target[1][1] - target[0][1]]
        area_index = get_index_multi(area, self.area_list)
        if len(area_index) == 1:  # 只有一个的情况
            return area_index[0]
        else:
            vec_index = get_index_multi(first_vec, self.first_vec_list)
            index = [x for x in area_index if x in vec_index]
            if len(index) == 0:
                return -1
            return index[0]  # 一般情况就只有一个了

    def getAllNFP(self):
        for i in range(len(self.polys)):
            for j in range(len(self.polys)):
                nfp = self.tryCreateNFP(i, j)
                self.nfp_list[i][j] = get_slide(
                    nfp, -self.centroid_list[i][0], -self.centroid_list[i][1]
                )

    def tryCreateNFP(self, i, j):
        bias_values = [1e-4, 7e-5, 4e-5, 1e-5]
        poly1 = self.polys[i]
        poly2 = self.polys[j]
        for bias_idx, bias in enumerate(bias_values):
            nfp_object = NFP(poly1, poly2, bias=bias)
            if not nfp_object.error_msg:
                # nfp_object.showResult()
                return nfp_object.nfp
            else:
                print(f"多边形索引{i}和{j}, {nfp_object.error_msg}.", end=" ")
                if bias_idx == len(bias_values) - 1:
                    raise Exception(f"bias值均无法计算多边形索引{i}和{j}的NFP")
                else:
                    print(f"bias调整: {bias} -> {bias_values[bias_idx+1]}")
                    continue

    def storeNFP(self):
        path = "history/nfp.csv"
        with open(path, "a+") as csvfile:
            writer = csv.writer(csvfile)
            for i in range(len(self.polys)):
                for j in range(len(self.polys)):
                    writer.writerows(
                        [[self.polys[i], self.polys[j], self.nfp_list[i][j]]]
                    )

    # 输入形状获得NFP
    def getDirectNFP(self, poly1, poly2, **kw):
        if "index" in kw:
            i = kw["index"][0]
            j = kw["index"][1]
            centroid = get_point(Polygon(self.polys[i]).centroid)
        else:
            # 首先获得poly1和poly2的ID
            i = self.getPolyIndex(poly1)
            j = self.getPolyIndex(poly2)
            centroid = get_point(Polygon(poly1).centroid)
        # 判断是否计算过并计算nfp
        if self.nfp_list[i][j] == 0:
            nfp = NFP(poly1, poly2).nfp
            # if self.store_nfp == True:
            #    with open("history/nfp.csv", "a+") as csvfile:
            #        writer = csv.writer(csvfile)
            #        writer.writerows([[poly1, poly2, nfp]])
            # return nfp
        else:
            return get_slide(self.nfp_list[i][j], centroid[0], centroid[1])
