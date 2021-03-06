# -*- coding: utf-8 -*-
import scrapy
from scrapeNews.items import ScrapenewsItem
from scrapeNews.settings import logger


class TimetechSpider(scrapy.Spider):

    name = 'timeTech'
    custom_settings = {
        'site_id':103,
        'site_name':'timeTech',
        'site_url':'http://time.com/section/tech/'
    }

    def __init__(self, offset=0, pages=4, *args, **kwargs):
        super(TimetechSpider, self).__init__(*args, **kwargs)
        for count in range(int(offset), int(offset) + int(pages)):
            self.start_urls.append('http://time.com/section/tech/?page='+ str(count+1))

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}, errback=self.errorRequestHandler)

    def errorRequestHandler(self, failure):
        logger.error(__name__ + ' Non-200 response at ' + str(failure.request.url))

    def parse(self, response):
        try:
            # For the large newsBox in top of all the pages. (In Normal Pages) or sends all request for all the articles in API page or sends the request for the special page.
            try:
                newsBox = 'http://www.time.com' + response.xpath("//div[@class='partial hero']/article/a/@href").extract_first()
                if not self.postgres.checkUrlExists(newsBox):
                    self.urls_parsed += 1
                    yield scrapy.Request(url=newsBox, callback=self.parse_article, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}, errback=self.errorRequestHandler)
                else:
                    self.urls_dropped += 1
        
            except Exception as Error:
         
                if newsBox.xpath("//main[contains(@class,'content article')]"):
                    self.urls_parsed += 1
                    yield scrapy.Request(url=newsBox, callback=self.parse_article, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}, errback=self.errorRequestHandler)

                elif newsBox.xpath("//div[contains(@class,'_29M-6C9w')]"):
                    newsContainer = newsBox.xpath("//div[contains(@class,'_29M-6C9w')]//div[contains(@class,'_2cCPyP5f')]//a[@class='_2S9ChopF']/@href")
                    for link in newsContainer:
                        if not self.postgres.checkUrlExists(link):
                            self.urls_parsed += 1
                            yield scrapy.Request(url=link, callback=self.parse_article, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}, errback=self.errorRequestHandler)
                        else:
                            self.urls_dropped += 1
                else:
                    logger.error(__name__ + " Unable to Extract Links from Top Box : " + response.url)

            # For the rest of the boxes
            newsContainer = response.xpath("//div[@class='partial marquee']/article")
            for newsBox in newsContainer:
                link = 'http://www.time.com' + newsBox.xpath('a/@href').extract_first()
                if not self.postgres.checkUrlExists(link):
                    self.urls_parsed += 1
                    yield scrapy.Request(url=link, callback=self.parse_article, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}, errback=self.errorRequestHandler)
                else: 
                    self.urls_dropped += 1
        except Exception as e:
            logger.error(__name__ + " [UNHANDLED] " + str(e) + " : " + response.url)


    def parse_article(self, response):
        try:
            item = ScrapenewsItem()  # Scraper Items
            item['image'] = self.getPageImage(response)
            item['title'] = self.getPageTitle(response)
            item['content'] = self.getPageContent(response)
            item['newsDate'] = self.getPageDate(response)
            item['link'] = response.url
            item['source'] = 103
            if item['title'] is not 'Error' and item['content'] is not 'Error' and item['newsDate'] is not 'Error':
                self.urls_scraped += 1
                yield item
            else:
                self.urls_dropped += 1
        except Exception as e:
            self.urls_dropped += 1
            logger.error(__name__ + " [UNHANDLED] " + str(e) + " : " + response.url)


    def getPageTitle(self, response):
        try:
            data = response.xpath('//h1[@itemprop="headline"]/text()').extract_first()
            if (data is None):
                data = response.xpath("//h1[contains(@class,'headline')]/text()").extract_first()
            if (data is None):
                data = response.xpath("//h1[@class='_8UFs4BVE']/text()").extract_first()
            if (data is None):
                data = response.xpath("//span[@class='xxx_oneoff_special_story_v3_headline']/text()").extract_first()
            if (data is None):
                logger.error(__name__ + " Unable to Extract Title  : " + response.url)
                data = 'Error'
        except Exception as e:
            logger.error(__name__ + " [UNHANDLED] Unable to Extract Title : " + str(e) + " : " + response.url)
            data = 'Error'
        return data

    def getPageImage(self, response):
        try:
            data = response.xpath("//meta[@property='og:image']/@content").extract_first()
            if (data is None):
                logger.error(__name__ + " Unable to Extract Image  : " + response.url)
                data = 'Error'
        except Exception as e:
            logger.error(__name__ + " [UNHANDLED] Unable to Extract Image : " + str(e) + " : " + response.url)
            data = 'Error'
        return data

    def getPageDate(self, response):
        try:
            # split used to Spit Data in Correct format!
            data = (str(response.xpath("//script[@type='application/ld+json']").extract_first()).split('datePublished":"',1)[1])[:19]
        except (TypeError,IndexError) as Error:
            # This fail case works only on very specific articles.
            scriptData = None
            scriptsList = response.xpath("/html/head/script[not(contains(@type,'text/javascript'))]")
            for script in scriptsList:
                try:
                    scriptData = (script.extract()).split("<script>utag_data",1)[1]
                    break
                except:
                    continue
            if (scriptData is not None):
                data = (scriptData.split('"publish_date":"',1)[1]).split("+",1)[0]
            if (data is None):
                logger.error(__name__ + " Unable to Extract Date : " + response.url)
                data = 'Error'
        except Exception as Error:
            logger.error(__name__ + " [UNHANDLED] Unable to Extract Date : " + str(Error) + " : " + response.url)
            data = 'Error'
        
        return data


    def getPageContent(self, response):
        try:
            data = ' '.join(response.xpath("//div[@id='article-body']/div/p/text()").extract())
            if not data:
                data = ' '.join(response.xpath("//section[@class='chapter']//text()").extract())
            if not data:
                data = ' '.join(response.xpath("//div[contains(@class,'-5s7sjXv')]/div/div/article/p/text()").extract())
            if not data:
                data = ' '.join(response.xpath("//div[contains(@class,'_1Joi0PLr')]//span/text()").extract())
            if not data:
                logger.error(__name__ + " Unable to Extract Content  : " + response.url)
                data = 'Error'
        except Exception as e:
            logger.error(__name__ + " [UNHANDLED] Unable to Extract Content : " + str(e) + " : " + response.url)
            data = 'Error'
        return data


# DEAD API's Link: 'http://time.com/wp-json/ti-api/v1/posts?time_section_slug=time-section-tech&_embed=wp:meta,wp:term,fortune:featured,fortune:primary_section,fortune:primary_tag,fortune:primary_topic&per_page=30&page1'
