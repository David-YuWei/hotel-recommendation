# -*- coding: utf-8 -*-
#item to item recommendation

import DB
import math

def main():
    #construct data
    #item dictionary
    item_dict = {}
    #item to customer dictionary
    item2C_dict = {}
    #customer to item dictionary
    c2Item_dict = {}
    item_list = DB.query("select * from hotel")
    print "item amount:" + str(len(item_list))
    for item in item_list:
        detail = {}
        detail["name"] = item["name_cn"]
        detail["latitude"] = item["latitude"]
        detail["longitude"] = item["longitude"]
        item_dict[item["id"]] = detail
        item2C_list = DB.query("select * from reviews_1 where hotelId = " + str(item["id"]))
        print "hotelId:" + str(item["id"]) + ", review amount:" + str(len(item2C_list))
        customers = set()
        for customer in item2C_list:
            if customer["user"] not in c2Item_dict:
                cItem_dict = {}
                cItem_dict[item["id"]] = customer["score"]
                c2Item_dict[customer["user"]] = cItem_dict
            else:
                if customer["user"] not in customers:
                    cItem_dict = c2Item_dict[customer["user"]]
                    cItem_dict[item["id"]] = customer["score"]
                    c2Item_dict[customer["user"]] = cItem_dict
            customers.add(customer["user"])
        item2C_dict[item["id"]] = customers
    # item to item recommendation using strategy like:
    # For each item in item_dict, I1
    #   For each customer C who purchased I1
    #       For each item I2 purchased by customer C
    #           Record that a customer purchased I1 and I2
    #   For each item I2
    #       Compute the similarity between I1 and I2 using cosine measure
    similarity = {}
    for item in item_dict:
        customers = item2C_dict[item]
        similarItem_dict = {}
        for customer in customers:
            cItems = c2Item_dict[customer]
            for cItem in cItems:
                if cItem != item:
                    if cItem not in similarItem_dict:
                        cList = []
                        cList.append(customer)
                        similarItem_dict[cItem] = cList
                    else:
                        cList = similarItem_dict[cItem]
                        cList.append(customer)
                        similarItem_dict[cItem] = cList
        #calculate similarity
        similar_dict = {}
        for sItem in similarItem_dict:
            sim = 0
            if sItem in similarity:
                sim_dict = similarity[sItem]
                sim = sim_dict[item]
            else:
                customers = similarItem_dict[sItem]
                i1 = []
                i2 = []
                for customer in customers:
                    cItems = c2Item_dict[customer]
                    i1.append(cItems[item])
                    i2.append(cItems[sItem])
                sim = __sim(i1,i2)
            similar_dict[sItem] = sim
        similarity[item] = similar_dict
    #print similarity
    item2item_recom = {}
    for sim in similarity:
        if similarity[sim]:
            lst = __bubbleSort(similarity[sim],10)
            item2item_recom[sim] = lst
    for recom in item2item_recom:
        print "recommendation for " + item_dict[recom]["name"].encode("utf-8") + ":"
        for item in item2item_recom[recom]:
            print item_dict[item]["name"]

    #print item2item_recom

def __bubbleSort(dict,topNum):
    res = []
    num = 0
    while num < topNum:
        if len(dict) == 0:
            break
        maxItem = dict.keys()[0]
        for item in dict:
            if dict[item] > dict[maxItem]:
                maxItem = item
        res.append(maxItem)
        del dict[maxItem]
        num += 1
    return res

#cosine similarity
def __sim(i1,i2):
    if len(i1) == 1:
        return 0.5
    sim = 0
    numerator = 0
    denominator1 = 0
    denominator2 = 0
    i = iter(i1)
    while True:
        try:
            m = i.next()
            denominator1 = denominator1 + m * m
        except StopIteration as s:
            break
    denominator1 = math.sqrt(denominator1)
    ii = iter(i2)
    while True:
        try:
            m = ii.next()
            denominator2 = denominator2 + m * m
        except StopIteration as s:
            break
    denominator2 = math.sqrt(denominator2)
    i = iter(i1)
    ii = iter(i2)
    while True:
        try:
            m = i.next()
            n = ii.next()
            numerator = numerator + m * n
        except StopIteration as e:
            break
    sim = numerator/(denominator1 * denominator2)
    return sim

if __name__ == '__main__':
    main()
    #print __sim([2.3,0,4],[4,8,3])

