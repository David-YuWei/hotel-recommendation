# -*- coding: utf-8 -*-
import requests
import json
import math
import DB
import Filter
import datetime
import urllib2
import random


from bs4 import BeautifulSoup
from datetime import timedelta
from abc import ABCMeta, abstractmethod
from Exceptions import ProjectException



class Crawler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

class CtripCrawler(Crawler):

    curl = "http://hotels.ctrip.com/Domestic/Tool/AjaxHotelList.aspx"
    eurl_prefix = "http://english.ctrip.com/hotels/beijing-hotel-detail-"
    creview_prefix = "http://hotels.ctrip.com/Domestic/tool/AjaxHotelCommentList.aspx"
    hotel_page_prefix = "http://hotels.ctrip.com/hotel/"
    ereview_prefix = ""
    dianping_search_hotel_url = "http://www.dianping.com/beijing/hotel/_"
    dianping_hotel_url = "http://www.dianping.com/shop/"
    #size = 0

    def start(self):
        payload = {}
        payload["cityName"] = "北京"
        payload["operationtype"] = "NEWHOTELORDER"
        payload["IsOnlyAirHotel"] = "F"
        payload["cityId"] = "1"
        payload["cityPY"] = "beijing"
        payload["cityCode"] = "010"
        payload["htlPageView"] = "0"
        payload["hotelType"] = "F"
        payload["hasPKGHotel"] = "F"
        payload["requestTravelMoney"] = "F"
        payload["isusergiftcard"] = "F"
        payload["useFG"] = "F"
        payload["priceRange"] = "-2"
        payload["promotion"] = "F"
        payload["prepay"] = "F"
        payload["IsCanReserve"] = "F"
        payload["OrderBy"] = "99"
        payload["markType"] = "0"
        payload["contrast"] = "0"
        payload["star"] = "4,5"
        #run 7 times (tomorrow, 10 days later, 20 days later, 30 days later, 60 days later, 90 days later, 180 days later)
        #to grab all the 4,5 star hotel data
        checkDate = {}
        checkDate[datetime.datetime.now() + timedelta(days=1)] = datetime.datetime.now() + timedelta(days=2)
        checkDate[datetime.datetime.now() + timedelta(days=10)] = datetime.datetime.now() + timedelta(days=11)
        checkDate[datetime.datetime.now() + timedelta(days=20)] = datetime.datetime.now() + timedelta(days=21)
        checkDate[datetime.datetime.now() + timedelta(days=30)] = datetime.datetime.now() + timedelta(days=31)
        checkDate[datetime.datetime.now() + timedelta(days=60)] = datetime.datetime.now() + timedelta(days=61)
        checkDate[datetime.datetime.now() + timedelta(days=90)] = datetime.datetime.now() + timedelta(days=91)
        checkDate[datetime.datetime.now() + timedelta(days=180)] = datetime.datetime.now() + timedelta(days=181)
        for (k,v) in checkDate.items():
            payload["StartTime"] = str(k)[0:10]
            payload["DepTime"] = str(v)[0:10]
            payload["checkIn"] = str(k)[0:10]
            payload["checkOut"] = str(v)[0:10]
            pageno = 1
            pageCount = 1
            while pageno <= pageCount:

                payload["page"] = str(pageno)
                source_code = requests.post(self.curl,payload)
                ids = source_code.text
                if pageno == 1:
                    startIdx = ids.index("\"hotelAmount\":")
                    endIdx = ids.index(",\"sortHeader\"")
                    dataCount = ids[startIdx+14:endIdx]
                    pageCount = math.ceil(int(dataCount) / 25.0)
                    print pageCount
                #get substring
                startIdx = ids.index("\"hotelPositionJSON\":[")
                endIdx =  ids.index(",\"biRecord")
                ids = "{"+ ids[startIdx:endIdx] +"}"
                ids = ids.replace('\\','/')
                plain_text = json.loads(ids)

                hotels = plain_text["hotelPositionJSON"]
                self.__save(hotels)
                print pageno
                pageno += 1

    def getNearbyFacilities(self):
        hotel_list = DB.query("select * from hotel");
        facility_type = DB.query("select * from facility_type")
        types = {}
        for type in facility_type:
            types[type["name"]] = type["id"]
        for hotel in hotel_list:
            hotel_id = hotel["originalHotelID"]
            print hotel_id
            hotel_url = self.hotel_page_prefix + hotel_id + ".html"
            page_code = requests.get(hotel_url)
            soup = BeautifulSoup(page_code.text, "html.parser")
            div_list = soup.find_all('div',{'class':'htl_info_table'})
            if len(div_list) == 0:
                continue
            div = div_list[len(div_list) -1]
            #print div
            tr_list = div.find_all('tr')
            for tr in tr_list:
                type = types[tr.find('th').string]
                print tr.find('th').string
                ctt = tr.find_all('li')
                if len(ctt) != 0:
                    for li in ctt:
                        sql = "insert into hotel_nearby_facility(hotel_id,type,name,sub_type) values("+str(hotel["id"])+","+str(type)+",\""+li.string+"\",0)"
                        print sql
                        DB.insert(sql)


    def getNearbyCateringInfo(self):
        hotel_list = DB.query("select * from hotel where id > 570");
        for hotel in hotel_list:
            hotel_id = hotel["id"]
            hotel_name = hotel["name_cn"]
            #hotel_name = "桔子水晶酒店（北京总部基地店)(原双赢酒店）"
            print hotel_name
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; zh-CN; rv:1.9.1.2) Gecko/20090803 Fedora/3.5.2-2.fc11 Firefox/3.5.2'
            }
            dianping_search_url = self.dianping_search_hotel_url+ hotel_name
            page_code = requests.get(dianping_search_url,headers = headers)
            soup = BeautifulSoup(page_code.text, "html.parser")
            #print soup
            ul = soup.find('ul',{'class':'hotelshop-list'})
            h2 = ul.find('h2',{'class':'hotel-name'})
            title = ''
            url = ''
            if h2 is not None:
                a = h2.find('a',{'class':'hotel-name-link'})
                title = a.string
                url = a['href']
                print title
                print url
            else:
                title = 'n/a'
                url = 'n/a'
            sql = "insert into hotel_dianping_info(id,name_cn,dianping_url,dianping_name) values("+str(hotel_id)+",\""+hotel_name+"\",\""+url+"\",\""+title+"\")"
            print sql
            DB.insert(sql)
            #break

    def getgetNearbyCateringInfo_other(self):
        hotel_list = DB.query("select * from hotel_dianping_info where id > 616 and dianping_url != 'n/a'");
        around_url = "http://www.dianping.com/search/around/2/10_"
        type={}
        type["火锅"] = "/g110d1"
        type["咖啡厅"] = "/g132d1"
        type["烧烤"] = "/g508d1"
        type["面包甜点"]="/g117d1"
        type["自助餐"]="/g111d1"
        type["日本菜"]="/g113d1"
        type["西餐"]="/g116d1"
        type["北京菜"]="/g311d1"
        type["韩国料理"]="/g114d1"
        type["海鲜"]="/g251d1"
        type["江浙菜"]="/g101d1"
        type["粤菜"]="/g103d1"
        type["清真菜"]="/g108d1"
        type["素菜"]="/g109d1"
        type["川菜"]="/g102d1"
        type["湘菜"]="/g104d1"
        type["新疆菜"]="/g3243d1"
        type["西北菜"]="/g26481d1"
        type["家常菜"]="/g1783d1"
        type["东北菜"]="/g106d1"
        proxy_support = urllib2.ProxyHandler({'http':'184.82.45.37:3128'})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)
        for hotel in hotel_list:
            hotel_id = hotel["id"]
            hotel_dianping_id = hotel["dianping_url"]
            hotel_dianping_id = hotel_dianping_id[6:]
            print hotel_dianping_id
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
                'Referer':'http://www.dianping.com/'
            }
            for (k,v) in type.items():
                #default: dianping_search_url = around_url + hotel_dianping_id + v
                #ordered by comment from customer
                dianping_search_url = around_url + hotel_dianping_id + v +"o3"
                #content = urllib2.urlopen(dianping_search_url).read()
                page_code = requests.get(dianping_search_url,headers = headers)
                soup = BeautifulSoup(page_code.text, "html.parser")
                #print soup
                div = soup.find('div',{'class':'bread J_bread'})
                count = div.find('span',{'class':'num'}).string
                count = str(count)[1:]
                count = count[:-1]
                score = 0
                if count != "0":
                    div = soup.find('div',{'id':'shop-all-list'})
                    li = div.find('li')
                    div = li.find('div',{'class':'comment'})
                    span = div.find('span')
                    comment = span['title']
                    if comment[0:1] == u'准':
                        score = -0.5
                        comment = comment[1:]
                    if comment[0:1] == u'五':
                        score += 5.0
                    elif comment[0:1] == u'四':
                        score += 4.0
                    elif comment[0:1] == u'三':
                        score += 3.0
                    elif comment[0:1] == u'二':
                        score += 2.0
                    elif comment[0:1] == u'一':
                        score += 1.0
                    else:
                        score = 0.0
                sql = "insert into hotel_nearby_catering(hotel_id,type,count,score) values("+str(hotel_id)+",\""+k+"\","+count+","+str(score)+")"
                print sql
                DB.insert(sql)
                #break

    def makeUserData(self):
        users = ['Yw','Kevin','Martin','Lee','David','Hj','Amy','Nick','Deniel',
                'Zack','William','Darcy','Emma','Emily','James','Michael','Olivia',
                'Sophia','Isebella','Ava','Mia','Abigail','Madison','Charlotte','Harper',
                'Sofia','Avery','Elizabeth','Amelia','Evelyn','Ella','Chloe','Victoria',
                'Aubrey','Grace','Zoey','Natalie','Addison','Lillian','Brooklyn',
                'Lily','Hannah','Layla','Scarlett','Aria','Zoe','Samantha','Anna','Leah',
                'Audrey','Ariana','Allison','Savannah','Arianna','Camila','Penelope',
                'Gabriella','Claire','Aaliyah','Sadie','Riley','Skylar','Nora','Sarah',
                'Hailey','Kaylee','Paisley','Kennedy','Ellie','Peyton','Annabelle',
                'Caroline','Madelyn','Serenity','Aubree','Lucy','Alexa','Alexis',
                'Nevaeh','Stella','Violet','Genesis','Mackenzie','Bella','Autumn',
                'Mila','Kylie','Maya','Piper','Alyssa','Taylor','Eleanor','Melanie',
                'Naomi','Faith','Eva','Katherine','Lydia','Brianna','Julia','Ashley','Khloe',
                'Madeline','Ruby','Sophie','Alexandra','London','Lauren','Gianna','Isabelle','Alice',
                'Vivian','Hadley','Jasmine','Morgan','Kayla','Cora','Bailey','Kimberly','Reagan','Hazel',
                'Clara','Sydney','Trinity','Natalia','Valentina','Rylee','Jocelyn',
                'Maria','Aurora','Eliana','Brielle','Liliana']
        hotel_list = DB.query("select c.hotel_id as id, h.rating_cn as rating, max(score) as mx from hotel_nearby_catering c, hotel h where c.hotel_id = h.id group by c.hotel_id");
        for user in users:
            score = 0
            count = 0
            for hotel in hotel_list:
                mx = hotel["mx"]
                rate = hotel["rating"]
                score = random.uniform(0,1)
                if score >= 0.7:
                    #count -= 1
                    #if count == 0:
                    #    break
                    if rate >= 4.2:
                        avg = random.randint(0,10)
                        if avg >= 4:
                            score = 1
                        else:
                            score = -1
                    else:
                        score = 0
                else:
                    score = 0
                if score != 0:
                    sql = "insert into user_hotel_rating(user_id,hotel_id,rating) values(\""+str(user)+"\","+str(hotel["id"])+","+str(score)+")"
                    #print sql
                    DB.insert(sql)
                    if score == 1:
                        count += 1
            sql_cuisine = "select * from ( select h.type as type, sum(h.score) as total from hotel_nearby_catering h where h.hotel_id in " \
                          "( select u.hotel_id from user_hotel_rating u where u.user_id = \""+str(user)+"\"" \
                            " and u.rating = 1 ) group by h.type) t order by t.total desc"
            min_score = 3.0 * count
            stats = DB.query(sql_cuisine)
            cuisine_list = []
            for stat in stats:
                if float(stat["total"]) >= min_score:
                    cuisine_list.append(stat["type"])
            l = len(cuisine_list)
            cuisines = []
            cuisines.append("北京菜")
            if l > 1:
                cuisines = random.sample(cuisine_list,2)
                print 'large'
            elif l == 1:
                cuisines = random.sample(cuisine_list,1)
                print 'equal'
            else:
                print 'zero'
            for cs in cuisines:
                sql_cuisine = "insert into user_favoriate_cuisine(user_id,cuisine) values(\""+str(user)+"\",\""+cs+"\")"
                print sql_cuisine
                DB.insert(sql_cuisine)


    def __save(self, hotels):
        for hotel in hotels:
            bfStr = hotel["name"] + hotel["lat"] + hotel["lon"]
            # Bloom Filter
            exist = Filter.isExist(bfStr)
            if not exist :
                #insert into database and get hotel's review
                id = hotel["id"]
                print id
                eurl = self.eurl_prefix + str(id) +"/"
                detail_code = requests.get(eurl)
                soup = BeautifulSoup(detail_code.text, "html.parser")
                en_name = soup.find('h1',{'itemprop':'name'}).string
                if en_name is None:
                    en_name = hotel["name"]
                en_score = soup.find('strong',{'itemprop':'ratingValue'})
                if en_score is None:
                    en_score = '3'
                else:
                    en_score = soup.find('strong',{'itemprop':'ratingValue'}).string
                star = 4
                if hotel["star"] == 'hotel_halfdiamond06':
                    star = 5.5
                elif hotel["star"] == 'hotel_stars05':
                    star = 5.0
                elif hotel["star"] == 'hotel_halfdiamond05':
                    star = 4.5
                elif hotel["star"] == 'hotel_stars04':
                    star = 4.0
                sql = "insert into hotel(name_cn,name_en,rating_cn,rating_en,starCount,latitude,longitude,originalHotelID,source) values(\"" \
                        + hotel["name"] +"\",\""+ en_name +"\","+ hotel["score"] +","+ en_score + ","+ str(star) + ",\"" \
                        + hotel["lat"] +"\",\""+hotel["lon"] +"\",\""+hotel["id"]+"\",\"c\")"
                print sql
                rowid = DB.insert(sql)
                print rowid
                self.__save_review(rowid,id)
                Filter.addItem(bfStr)

    def __save_review(self,rowid,hotelid):
        reviewUrl = self.creview_prefix + "?hotel=" + str(hotelid) + "&orderBy=2&currentPage="
        pageno = 1
        pageCount = 1
        empty = False
        while pageno <= pageCount:
            source_code = requests.get(reviewUrl + str(pageno))
            soup = BeautifulSoup(source_code.text,'html.parser')
            if pageno == 1:
                if soup.find(id='cTotalPageNum') is not None:
                    pageCount = int(soup.find(id='cTotalPageNum').get('value'))
            if empty:
                print 'no data left!'
                break
            for div in soup.find_all('div',{'class':'comment_block J_asyncCmt'}):
                try:
                    user = div.find('p',{'class':'name'}).string
                    if user == u'艺龙网用户':
                        empty = True
                        break
                    reviewTime = ""
                    if div.find('span',{'class':'score'}) is None:
                        #score = "-1"
                        #reviewTime = div.find('span',{'name':'needTraceCode'}).string
                        continue
                    else:
                        score = div.find('span',{'class':'n'}).string
                        reviewTime = div.find('a',{'name':'needTraceCode'}).string
                        reviewTime = reviewTime[3:]
                    reviewTime = datetime.datetime.strptime(str(reviewTime), "%Y-%m-%d")
                    comment = div.find('div',{'class':'J_commentDetail comment_txt_detail'}).string
                    comment = comment.replace("\"","'")
                    sql = "insert into reviews(user,score,comment,reviewTime,hotelId) " \
                          "values(\""+user+"\","+score+",\""+comment+"\",\""+str(reviewTime)+"\","+str(rowid)+")"
                    print sql
                    DB.insert(sql)
                except:
                    print "insert review error!" + sql
                    continue
            pageno +=1

    def stop(self):
            print("stopped!")



class CrawlerFactory():
    crawlers = {
        "ctrip": CtripCrawler()
    }

    @classmethod
    def createCrawler(cls,name):
        if name in cls.crawlers:
            return cls.crawlers[name]
        else:
            raise ProjectException("No such crawler: " + name)


