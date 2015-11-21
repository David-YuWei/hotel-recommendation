#!/usr/bin/env python
# Master's project 2015 fall University at Albany
# Hotel recommandation system

import sys

from Crawler import CrawlerFactory


def main():
    status = 0
    try:
        ctrip = CrawlerFactory.createCrawler("ctrip")
        qunar = CrawlerFactory.createCrawler("qunar")
        ctrip.start()
        #qunar.start()
    except Exception as e:
        print e
        status = 1

    return status

if __name__ == "__main__":
   sys.exit(main())

