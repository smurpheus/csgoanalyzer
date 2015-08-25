from codecs import open
import threading 
import requests
import time
conditions = ["Battle-Scarred", "Field-Tested", "Well-Worn", "Minimal Wear", "Factory New"]
collections = ["The Alpha Collection","The Assault Collection","The Aztec Collection","The Baggage Collection","The Bank Collection","The Cache Collection","The Chop Shop Collection","The Cobblestone Collection","The Dust Collection","The Dust 2 Collection","The Gods and Monsters Collection","The Inferno Collection","The Italy Collection","The Lake Collection","The Militia Collection","The Mirage Collection","The Nuke Collection","The Office Collection","The Overpass Collection","The Rising Sun Collection","The Safehouse Collection","The Train Collection","The Vertigo Collection"]
baseurl = "http://steamcommunity.com/market/priceoverview/?appid=730&currency=3&market_hash_name="
fname = "C:\Users\mher\Documents\csgoitems1.csv"

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


class ItemGrabber(threading.Thread):
    itemprices = {}
    items = []
    lock = threading.Lock()
    timedout = 0
    def __init__(self, items):
        threading.Thread.__init__(self)
        self.items = items
    
    @classmethod
    def getItems(self):
        items = []
        with open(fname, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                collection, weapon, skin, quality, stattrak = line.split(";")#
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
            if tryn < 10:
                r = requests.get(url)
                result = r.json()
                if result["success"] == True:
                    return result
                else:
                    return False
            else:
                print("Timedout Lal")
                self.timedout += 1
        except Exception e:
            time.sleep(1)
            self.queryPrices(url, tryn+1)
    
    def run(self):
        for collection, weapon, skin, quality, stattrak in self.items:
            for cond in conditions:
                url = self.generateURL(weapon, skin, stattrak, cond)
                response = self.queryPrices(url)
                ItemGrabber.lock.acquire()
                if response != False:
                    self.itemprices[(collection, weapon, skin, stattrak, cond)] = response
                ItemGrabber.lock.release() 
            
items = list(chunks(ItemGrabber.getItems(), 30))
threads = [] 
for chunk in items:
    thread = ItemGrabber(chunk) 
    threads += [thread] 
    thread.start() 
allitemprices = {}
totaltimeouts = 0
for x in threads: 
    x.join()
    totaltimeouts += x.timedout
    for key in x.itemprices.keys():
        allitemprices[key] = x.itemprices[key]
print(sorted(allitemprices.keys(),key=lambda x: x[0]))
print(len(allitemprices))
print(totaltimeouts)
