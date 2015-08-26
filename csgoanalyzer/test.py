from codecs import open
from os import path
import threading 
import requests
import json
import time
conditions = ["Battle-Scarred", "Field-Tested", "Well-Worn", "Minimal Wear", "Factory New"]
collections = ["The Alpha Collection", "The Assault Collection", "The Aztec Collection", "The Baggage Collection",
               "The Bank Collection", "The Cache Collection", "The Chop Shop Collection", "The Cobblestone Collection",
               "The Dust Collection", "The Dust 2 Collection", "The Gods and Monsters Collection",
               "The Inferno Collection", "The Italy Collection", "The Lake Collection", "The Militia Collection",
               "The Mirage Collection", "The Nuke Collection", "The Office Collection", "The Overpass Collection",
               "The Rising Sun Collection", "The Safehouse Collection", "The Train Collection",
               "The Vertigo Collection"]
baseurl = "http://steamcommunity.com/market/priceoverview/?appid=730&currency=3&market_hash_name="

fname = "csgoitems1.csv"

fname = path.join(path.dirname(path.abspath(__file__)), fname)
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in list(range(0, len(l), n)):
        yield l[i:i+n]


class ItemGrabber(threading.Thread):
    lock = threading.Lock()
    timedout = 0
    def __init__(self, items):
        self.items = []
        self.itemprices = {}
        threading.Thread.__init__(self)
        self.items = items
    
    @classmethod
    def getItems(self):
        items = []
        with open(fname, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                collection, weapon, skin, quality, stattrak = line.split(";")
                stattrak = stattrak.replace("\r", "").replace("\n", "")
                items.append((collection, weapon, skin, quality, stattrak))
        return items
        
    def generateURL(self, weapon, skin, stattrak, condition):
        if stattrak == "stattrak":
            query =  u"StatTrak™%%20%s%%20|%%20%s%%20(%s)"%(weapon,skin,condition)
        else:
            query =  "%s%%20|%%20%s%%20(%s)"%(weapon,skin,condition)
        query = query.replace(" ", "%20")
        url = "%s%s"%(baseurl, query)
        return url
        
    def queryPrices(self, url, tryn=1):
        try:
            if tryn < 1000:
                r = requests.get(url)
                result = r.json()
                if result["success"] == True:
                    return result
                else:
                    return False
            else:
                print("Timedout Lal")
                self.timedout += 1
        except Exception as e:
            #time.sleep(0.1)
            self.queryPrices(url, tryn+1)
    
    def run(self):
        for collection, weapon, skin, quality, stattrak in self.items:
            for cond in conditions:
                url = self.generateURL(weapon, skin, stattrak, cond)
                response = self.queryPrices(url)
                ItemGrabber.lock.acquire()
                if response != False:
                    self.itemprices[(collection, weapon, skin, quality, stattrak, cond)] = response
                ItemGrabber.lock.release()


class Analyzer(object):
    allitemprices = {}

    def __init__(self, read):
        resultname = "currentprices.csv"

        resultname = path.join(path.dirname(path.abspath(__file__)), resultname)
        if read:
            items = list(chunks(ItemGrabber.getItems(), 40))
            threads = []
            for chunk in items:
                thread = ItemGrabber(chunk)
                threads += [thread]
                thread.start()
            totaltimeouts = 0
            while len(threads) > 0:
                x = threads[0]
                if not x.isAlive():
                    x.join()
                    threads.pop(0)
                    totaltimeouts += x.timedout
                    for key in x.itemprices.keys():
                        self.allitemprices[key] = x.itemprices[key]

            with open(resultname, "w", encoding="utf-8") as f:
                f.write(str(self.allitemprices))
        else:
            with open(resultname, "r", encoding="utf-8") as f:
                lines = f.readlines()[0]
                self.allitemprices = json.loads(lines)




    def getLowestBuy(self, collection, quality, wear, stattrak):
        items = self.allitemprices.keys()
        filtered = filter(lambda x: collection in x[0] and quality in x[3] and wear in x[5] and stattrak in x[4], items)
        lowestprice = None
        lowestitem = None
        for item in filtered:
            price = self.allitemprices[item]
            pricenum = float(price["lowest_price"].replace(u"\u20AC", "").replace(",", "."))
            if lowestprice is None or lowestprice > pricenum:
                lowestprice = pricenum
                lowestitem = item
        return lowestitem, lowestprice

a = Analyzer(False)
a.getLowestBuy("Gods and Monsters", "Consumer", "Factory New", "")