def delete_redundancy(arr):
    new_arr = []
    for item in arr:
        if not item in new_arr:
            new_arr.append(item)
    return new_arr


def get_index_multi(item, _list):
    index_list = []
    for i in range(len(_list)):
        if item == _list[i]:
            index_list.append(i)
    return index_list
