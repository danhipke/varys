from scrapy.http import HtmlResponse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest, SplashJsonResponse, SplashTextResponse

from varys.items import ProductUrlItem

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


    def __init__(self, pdp_link_css_selector, paginate_link_css_selector, *a, **kw):
        rules = (
            Rule(LinkExtractor(allow=(), restrict_css=(paginate_link_css_selector)),
                 follow=True),)
        self.pdp_link_css_selector = pdp_link_css_selector
        self.paginate_click_script = """function main(splash)
            local url = splash.args.url
            assert(splash:go(url))
            assert(splash:wait(10))

            assert(splash:runjs("$('""" + paginate_link_css_selector + """')[0].click()"))
            assert(splash:wait(10))

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
        print('Processing..' + response.url)
        for product_url in response.css(self.pdp_link_css_selector).extract():
            item = ProductUrlItem()
            item['url'] = product_url
            yield item
        yield SplashRequest(url=response.url, callback=self.get_url, endpoint="execute", args={'lua_source': self.paginate_click_script})

        #if isinstance(response, (HtmlResponse, SplashTextResponse)):
        #    seen = set()
        #    for n, rule in enumerate(self._rules):
        #        links = [lnk for lnk in rule.link_extractor.extract_links(response)
        #                 if lnk not in seen]
        #        if links and rule.process_links:
        #            links = rule.process_links(links)
        #        for link in links:
        #            seen.add(link)
                    #r = SplashRequest(url=link.url, callback=self.parse_items, endpoint='render.html',
                    #                    args={'wait': 0.5})
        #            r = SplashRequest(url=link.url, callback=self.parse_items, endpoint='execute',
        #                              args={'wait': 0.5, 'lua_source': self.paginate_click_script})
        #            #r.meta.update(rule=n, link_text=link.text)
        #            yield rule.process_request(r)

    def get_url(self, response):
        yield SplashRequest(url=response.body_as_unicode(), callback=self.parse_items, endpoint='render.html',
                                args={'wait': 0.5})
