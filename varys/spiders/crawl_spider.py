from scrapy.http import HtmlResponse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest, SplashJsonResponse, SplashTextResponse
from varys.items import SearchResultsItem
import re

infinite_scroll_script = """function main(splash)
    local num_scrolls = 10
    local scroll_delay = 1.0

    local scroll_to = splash:jsfunc("window.scrollTo")
    local get_body_height = splash:jsfunc(
        "function() {return document.body.scrollHeight;}"
    )
    assert(splash:go(splash.args.url))
    splash:wait(splash.args.wait)

    for _ = 1, num_scrolls do
        scroll_to(0, get_body_height())
        splash:wait(scroll_delay)
    end        
    return splash:html()
end"""

class VarysCrawlSpider(CrawlSpider):
    def __init__(self, pdp_link_css_selector, paginate_link_css_selector,
                 facet_div_css_selector, facet_label_css_selector, facet_value_css_selector,
                 result_tile_css_selector, result_title_css_selector,
                 result_price_css_selector, *a, **kw):
        rules = (
            Rule(LinkExtractor(allow=(), restrict_css=(paginate_link_css_selector)),
                 follow=True),)
        self.pdp_link_css_selector = pdp_link_css_selector
        self.facet_div_css_selector = facet_div_css_selector
        self.facet_label_css_selector = facet_label_css_selector
        self.facet_value_css_selector = facet_value_css_selector
        self.paginate_link_css_selector = paginate_link_css_selector
        self.result_tile_css_selector = result_tile_css_selector
        self.result_title_css_selector = result_title_css_selector
        self.result_price_css_selector = result_price_css_selector
        self.seen_facet_label_value_pairs = set()
        self.paginate_click_script = """function main(splash)
            local url = splash.args.url
            assert(splash:go(url))
            assert(splash:wait(3))

            assert(splash:runjs("$('""" + paginate_link_css_selector + """')[0].click()"))
            assert(splash:wait(3))

            return splash:url() 
        end"""
        super(VarysCrawlSpider, self).__init__(rules=rules, *a, **kw)



    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url=url, callback=self.parse_items, endpoint='render.html',
                                args={'wait': 0.5})
            #yield SplashRequest(url=url, callback=self.parse_items, endpoint='execute',
            #            args={'wait': 0.5, 'lua_source': self.paginate_click_script})
            #yield SplashRequest(url=url, callback=self.parse_items, endpoint='execute',
            #                args={'wait': 0.5, 'lua_source': script})

    def parse_items(self, response):
        #print('Processing..' + response.url)
        facet_label = response.meta.get('facet_label', None)
        facet_value = response.meta.get('facet_value', None)
        for product_tile in response.css(self.result_tile_css_selector):
            item = SearchResultsItem()
            item['facet_label'] = facet_label
            item['facet_value'] = facet_value
            item['url'] = product_tile.css(self.pdp_link_css_selector).extract_first()
            all_result_title_text = ''
            for result_title in product_tile.css(self.result_title_css_selector + '::text').extract():
                all_result_title_text += result_title.strip()
            item['title'] = all_result_title_text

            all_result_price_text = ''
            for result_price in product_tile.css(self.result_price_css_selector + '::text').extract():
                all_result_price_text += result_price.strip()
            item['price'] = all_result_price_text
            yield item
        #Uncomment this to crawl past first page
        #yield SplashRequest(url=response.url, callback=self.get_url, endpoint="execute", args={'lua_source': self.paginate_click_script})

        paginate_url = response.css(self.paginate_link_css_selector + '::attr(href)').extract_first()
        if paginate_url is not None:
            paginate_url = paginate_url.strip()
            paginate_request = SplashRequest(url=paginate_url, callback=self.parse_items, endpoint='render.html',
                                             args={'wait': 0.5})
            paginate_request.meta['facet_label'] = facet_label
            paginate_request.meta['facet_value'] = facet_value
            yield paginate_request


        for facet in response.css(self.facet_div_css_selector):
            all_facet_label_text = ''
            for facet_label in facet.css(self.facet_label_css_selector):
                for facet_label_text in facet_label.css('::text').extract():
                    all_facet_label_text += facet_label_text.strip()
                #print all_facet_label_text
            for facet_value in facet.css(self.facet_value_css_selector):
                all_facet_value_text = ''
                for facet_value_text in facet_value.css('::text').extract():
                    all_facet_value_text += facet_value_text.strip()
                all_facet_value_text = re.sub('\([^)]*\)', '', all_facet_value_text)
                #print all_facet_value_text
                url = facet_value.css('::attr(href)').extract_first().strip()
                #print url
                set_key = all_facet_label_text + '|||' + all_facet_value_text
                # Probably need to fix this. Doesn't support precedence rules or hierarchical facet values with the same name
                if set_key not in self.seen_facet_label_value_pairs:
                    self.seen_facet_label_value_pairs.add(set_key)
                    facet_request = SplashRequest(url=url, callback=self.parse_items, endpoint='render.html',
                                        args={'wait': 0.5})
                    facet_request.meta['facet_label'] = all_facet_label_text
                    facet_request.meta['facet_value'] = all_facet_value_text
                    yield facet_request
                #else:
                    #print 'Skipping ' + url

    def get_url(self, response):
        yield SplashRequest(url=response.body_as_unicode(), callback=self.parse_items, endpoint='render.html',
                                args={'wait': 0.5})
