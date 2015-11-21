# -*- coding: utf-8 -*-
import requests
import json
import math
import DB
import Filter
import datetime


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
    ereview_prefix = ""
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


class QunarCrawler(Crawler):

	def start(self):
		print("qunar started!")

	def stop(self):
		print("qunar stopped!")


class CrawlerFactory():
    crawlers = {
        "ctrip": CtripCrawler(),
        "qunar": QunarCrawler()
    }

    @classmethod
    def createCrawler(cls,name):
        if name in cls.crawlers:
            return cls.crawlers[name]
        else:
            raise ProjectException("No such crawler: " + name)


