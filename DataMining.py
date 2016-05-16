# -*- coding: utf-8 -*-


import DB
import math
import gv
import copy
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn import cross_validation

class hotel:
    def __init__(self, id, score, count):
        self.id = id
        self.score = score
        self.count = count

    def __lt__(self, other):
        if self.score < other.score:
            return True
        elif self.score == other.score:
            if self.count < other.count:
                return True
            else:
                return False
        else:
            return False

    def __eq__(self, other):
        return self.score == other.score and self.count == other.count

#item to item recommendation
def item2item():
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

def recommendWithFavor():
    hotel_sql = "select id,name_cn from hotel_dianping_info where dianping_name != 'n/a'"
    catering_count_sql = "select hotel_id, sum(count) as ct from hotel_nearby_catering group by hotel_id"
    user_sql = "select user_id from user_hotel_rating group by user_id"
    user_rating = "select user_id, hotel_id from user_hotel_rating where rating = 1"
    hotels_list = DB.query(hotel_sql)
    hotels_catering = DB.query(catering_count_sql)
    users_list = DB.query(user_sql)
    rating_list = DB.query(user_rating)
    hotels = {}
    caterings = {}
    users = []
    users_rating = set([])
    for htl in hotels_list:
        hotels[htl["id"]] = htl["name_cn"]
    for c in hotels_catering:
        caterings[c["hotel_id"]] = c["ct"]
    for user in users_list:
        users.append(user["user_id"])
    users_set = set(users)
    users_len = len(users)
    gv_len = len(gv.cuisine)
    for r in rating_list:
        users_rating.add(str(r["user_id"]) + "-" + str(r["hotel_id"]))
    while True:
        #name = "Yw"
        name = raw_input("Enter your name:")

        favor = raw_input("Below are several categories of cuisine, which one or more of them do you like."
                      "\n1 - 粤菜, 2 - 家常菜, 3 - 咖啡厅, 4 - 川菜, 5 - 海鲜, 6 - 湘菜, 7 - 新疆菜,"
                      "\n8 - 江浙菜, 9 - 韩国料理, 10 - 烧烤, 11 - 东北菜,12 - 西餐, 13 - 火锅,"
                      "\n14 - 北京菜, 15 - 面包甜点, 16 - 西北菜, 17 - 自助餐, 18 - 清真菜, 19 - 素菜, 20 - 日本菜."
                      "\nenter numbers with commas between:")
        #favor = "1,15"
        favors = favor.split(",")
        #get hotels which has a total score more than 2.5 * count(favors)

        limit_hotel_sql = "select hotel_id, sum(score) as rating from hotel_nearby_catering where type in ("
        valid_count = 0
        try:
            for f in favors:
                if int(f) <= gv_len:
                    limit_hotel_sql += "\""+gv.cuisine[int(f)-1] + "\","
                    valid_count += 1
        except Exception as e:
            print "error format in \""+favor+"\" , please enter valid parameters!"
            continue
        limit_hotel_sql = limit_hotel_sql[:-1] + ") group by hotel_id"
        print limit_hotel_sql
        hotels_rating = DB.query(limit_hotel_sql)
        potential_hotels = []
        min_score = 2.5 * valid_count
        for hr in hotels_rating:
            if hr["rating"] >= min_score:
                potential_hotels.append(hr["hotel_id"])
        hotel_len = len(potential_hotels)
        data = [[(1 if (str(i) + "-" + str(j) in users_rating) else 0) for j in potential_hotels] for i in users]
        u = 0
        if name in users_set:
            #old user
            #initialize data
            u = users.index(name)
        else:
            #new user
            data.append([0 for q in potential_hotels])
            u = users_len
        pred = copy.deepcopy(data)
        for m in range(0,hotel_len):
            if pred[u][m] == 0 :
                x = []
                y = []
                for row in range(0,users_len):
                    if row != u:
                        x.append(data[row][:m]+data[row][m+1:])
                        y.append(data[row][m])
                try:
                    lr = LogisticRegression()
                    lr.fit(x,y)
                    val = lr.predict_proba(data[u][:m]+data[u][m+1:])
                    pred[u][m] = round(val[0][1],2)
                except Exception as e:
                    pred[u][m] = 0
        #recommend hotels
        recommend_hotel_unsorted = []
        for idx in range(0,hotel_len):
            if data[u][idx] == 0:
                recommend_hotel_unsorted.append(hotel(potential_hotels[idx], pred[u][idx], caterings[potential_hotels[idx]]))
        #for rhu in recommend_hotel_unsorted:
        #    print rhu.score
        result = __topN(recommend_hotel_unsorted, 10)
        for res in result:
            print hotels[res.id]
            print res.score
            #print res.count

def evaluate():
    users_ratings = DB.query("select user_id, hotel_id, rating from user_hotel_rating")
    hotels_list = DB.query("SELECT hotel_id FROM user_hotel_rating group by hotel_id")
    hotels = []
    for htl in hotels_list:
        hotels.append(htl["hotel_id"])
    total = len(users_ratings)
    kf_total = cross_validation.ShuffleSplit(total, n_iter=20, test_size=0.1,random_state=0)
    hotel_len = len(hotels)
    index = 0
    oa_tp = 0
    oa_tn = 0
    oa_fp = 0
    oa_fn = 0
    oa_n_tp = 0
    oa_n_tn = 0
    oa_n_fp = 0
    oa_n_fn = 0
    for train, test in kf_total:
        train_data = []
        test_data = []
        users_rating = set([])
        users = []
        for idx in test:
            test_data.append(users_ratings[idx])
        for idx in train:
            if users_ratings[idx]["rating"] == 1:
                users_rating.add(str(users_ratings[idx]["user_id"]) + "-" + str(users_ratings[idx]["hotel_id"]))
            if users_ratings[idx]["user_id"] not in users:
                users.append(users_ratings[idx]["user_id"])
        users_len = len(users)
        #standard logistical regression
        data = [[(1 if (str(i) + "-" + str(j) in users_rating) else 0) for j in hotels] for i in users]
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        for t in test_data:
            u = 0
            if t["user_id"] in users:
                #old user
                #initialize data
                u = users.index(t["user_id"])
            else:
                #new user
                data.append([0 for q in hotels])
                u = users_len
            m = hotels.index(t["hotel_id"])
            x = []
            y = []
            for row in range(0,users_len):
                if row != u:
                    x.append(data[row][:m]+data[row][m+1:])
                    y.append(data[row][m])
            pred = 0
            try:
                lr = LogisticRegression()
                lr.fit(x,y)
                val = lr.predict_proba(data[u][:m]+data[u][m+1:])
                pred = round(val[0][1],2)
            except Exception as e:
                pred = 0
            #print pred
            if pred >= 0.3:
                if t["rating"] == 1:
                    tp += 1
                    oa_tp +=1
                else:
                    fp += 1
                    oa_fp +=1
            else:
                if t["rating"] == 1:
                    fn += 1
                    oa_fn +=1
                else:
                    tn += 1
                    oa_tn +=1
        precision = float(tp) / (tp + fp)
        recall = float(tp) / (fn + tp)
        f_measure = 2 * precision *recall/(precision + recall)
        DB.insert("insert into evaluation(pcision,recall,f_measure,pair_idx,new_method) values("+str(precision)+","+str(recall)+","+str(f_measure)+","+str(index)+",\"old\")")
        #favoriate-based logistical regression
        n_tp = 0
        n_tn = 0
        n_fp = 0
        n_fn = 0
        for t in test_data:
            limit_hotel_sql = "select hotel_id, sum(score) as rating, count(1) as ct from hotel_nearby_catering where type in (select cuisine from user_favoriate_cuisine where user_id = \""+t["user_id"]+"\") group by hotel_id"
            #print limit_hotel_sql
            hotels_rating = DB.query(limit_hotel_sql)
            potential_hotels = []
            for hr in hotels_rating:
                if hr["rating"] >= 2.5*hr["ct"]:
                    potential_hotels.append(hr["hotel_id"])
            hotel_len = len(potential_hotels)
            data = [[(1 if (str(i) + "-" + str(j) in users_rating) else 0) for j in potential_hotels] for i in users]
            u = 0
            if t["user_id"] in users:
                #old user
                #initialize data
                u = users.index(t["user_id"])
            else:
                #new user
                data.append([0 for q in hotels])
                u = users_len
            pred = 0
            if t["hotel_id"] not in potential_hotels:
                pred = 0
            else:
                m = potential_hotels.index(t["hotel_id"])
                x = []
                y = []
                for row in range(0,users_len):
                    if row != u:
                        x.append(data[row][:m]+data[row][m+1:])
                        y.append(data[row][m])
                try:
                    lr = LogisticRegression()
                    lr.fit(x,y)
                    val = lr.predict_proba(data[u][:m]+data[u][m+1:])
                    pred = round(val[0][1],2)
                except Exception as e:
                    pred = 0
                #print pred
            if pred >= 0.3:
                if t["rating"] == 1:
                    n_tp += 1
                    oa_n_tp +=1
                else:
                    n_fp += 1
                    oa_n_fp +=1
            else:
                if t["rating"] == 1:
                    n_fn += 1
                    oa_n_fn +=1
                else:
                    n_tn += 1
                    oa_n_tn +=1
        n_precision = float(n_tp) / (n_tp + n_fp)
        n_recall = float(n_tp) / (n_fn + n_tp)
        n_f_measure = 2 * n_precision *n_recall/(n_precision + n_recall)
        DB.insert("insert into evaluation(pcision,recall,f_measure,pair_idx,new_method) values("+str(n_precision)+","+str(n_recall)+","+str(n_f_measure)+","+str(index)+",\"new\")")
        index += 1
    oa_precision = float(oa_tp) / (oa_tp + oa_fp)
    oa_recall = float(oa_tp) / (oa_fn + oa_tp)
    oa_f_measure = 2 * oa_precision *oa_recall/(oa_precision + oa_recall)
    oa_n_precision = float(oa_n_tp) / (oa_n_tp + oa_n_fp)
    oa_n_recall = float(oa_n_tp) / (oa_n_fn + oa_n_tp)
    oa_n_f_measure = 2 * oa_n_precision *oa_n_recall/(oa_n_precision + oa_n_recall)
    DB.insert("insert into evaluation(pcision,recall,f_measure,pair_idx,new_method) values("+str(oa_precision)+","+str(oa_recall)+","+str(oa_f_measure)+",-1,\"total_old\")")
    DB.insert("insert into evaluation(pcision,recall,f_measure,pair_idx,new_method) values("+str(oa_n_precision)+","+str(oa_n_recall)+","+str(oa_n_f_measure)+",-1,\"total_new\")")

def __topN(list, num):
    __buildHeap(list)
    l = len(list)
    result = []
    for i in range(0,num):
        __heapify(list, 0 , l - i - 1)
        result.append(list[0])
        tmp = list[0]
        list[0] = list[l - i - 1]
        list[l - i -1] = tmp
    return result

def __buildHeap(list):
    l = len(list)
    begin = l / 2 - 1
    for i in range(begin, -1, -1):
        left = 2*i + 1
        right = 2*i + 2
        if right >= l :
            if list[i] < list[left]:
                tmp = list[i]
                list[i] = list[left]
                list[left] = tmp
                __heapify(list,left,l-1)
        else:
            pos = left
            if list[left] < list[right] :
                pos = right
            if list[i] < list[pos]:
                tmp = list[i]
                list[i] = list[pos]
                list[pos] = tmp
                __heapify(list,pos,l-1)

def __heapify(list, start, end):
    if start >= end:
        return
    left = 2*start + 1 if 2*start + 1 <= end else -1
    right = 2*start + 2 if 2*start +2 <= end else -1

    if left == -1:
        return
    elif right == -1:
        if list[start] < list[left]:
                tmp = list[start]
                list[start] = list[left]
                list[left] = tmp
    else:
        pos = left
        if list[left] < list[right] :
            pos = right
        if list[start] < list[pos]:
            tmp = list[start]
            list[start] = list[pos]
            list[pos] = tmp
            __heapify(list,pos,end)


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
    #item2item()
    #recommendWithFavor()
    evaluate()

