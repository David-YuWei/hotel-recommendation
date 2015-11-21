# check if hotel related information has already been grabbed from somewhere
# m = - nlogp / (log2)^2
# false positive probability =  m/n log(2)
# m = number of bits for the bloom filter
# n = how many hotels we are planning to keep in the bloom filter
# p = desired false positive probability

import DB

from pybloom import BloomFilter

n = 5000
p = 0.01
bf = BloomFilter(n,p)

#init bf by selecting data from database
list = DB.query("select name_cn, latitude, longitude from hotel")

for l in list:
	hotelStr = l["name_cn"] + l["latitude"] + l["longitude"]
	#print(hotelStr)
	bf.add(hotelStr)

def isExist(test_str):
	return (test_str in bf)

def addItem(itemStr):
	return bf.add(itemStr)