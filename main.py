from bs4 import BeautifulSoup
import asyncio,aiohttp,time,datetime
from const import *

class economicCalendar():
    def __init__(self,chatID,tokenTG,link):
        self.__chatID = chatID
        self.__tokenTG = tokenTG
        self.__arrEconomicCalendar = []
        self.__link = link


    async def get_economic_calendar(self):
        async with aiohttp.ClientSession() as session:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'} 
            async with session.post(self.__link,headers=headers) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                return soup 


    async def parse_economic_calendar(self,soup): 
        
        data = soup.find('table', {'id': 'economicCalendarData'}) 

        tbody = data.find('tbody') 

        jsParse = tbody.findAll('tr', {'class': 'js-event-item'}) 

        for js in jsParse:

            # Время события
            timeEvent = js.attrs['data-event-datetime']

            # Страна события
            curr = js.find('td', {'class': 'flagCur'})
            for x in curr:
                if len(x) == 4:
                    curr = x
           
            # Важность
            sent = js.find('td', {'class': 'sentiment'})
            sentTo = sent['title']

            # Событие
            eventsA = js.find('td', {'class': 'event'})
            eventsTo = eventsA.find('a') 

            data = {'time' : timeEvent,'currency' : curr,'importance' : sentTo, 'text' : eventsTo.text.strip(),'link' : 'https://ru.investing.com' + eventsTo['href']}
            self.__arrEconomicCalendar.append(data)

    async def sendMessageTelegram(self,msg):
        data = { 
            "chat_id": self.__chatID, # 
            "text": msg
        }

        token = self.__tokenTG

        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.telegram.org/bot1853282626:AAGLzTRzkOAMgOVXpxAwa-ar6HWr1v4R_co/sendMessage',data=data) as response:
                await response.json()

    def datetime_to_hour_minute(self,time):
        spl = time.split(' ')[1].split(':')
        mh  = spl[0] +':'+ spl[1]
        return mh

    def importance_to_smile(self,imp):
        string = ''

        if imp.find('высокая') != -1:
            string = '🔹🔹🔹'
        elif imp.find('умеренная') != -1:
            string = '🔹🔹'
        else: # низкая
            string = '🔹'

        return string

    def check_times(self,timeE):
        
        localTime = time.time()
        eventTime = time.mktime(datetime.datetime.strptime(timeE, "%Y/%m/%d %H:%M:%S").timetuple())
        timeToSec = eventTime - localTime
        
        if (timeToSec > 0) and (timeToSec < 300): # five minutes
            return True

        return False


    def str_format(self,time,imp,cur,text):
        string_event = self.datetime_to_hour_minute(time)\
        + '  | ' + self.importance_to_smile(imp) + ' | '\
        + cur + '\n'\
        + text + '\n\n'
        return string_event

    async def loop(self):

        await self.parse_economic_calendar(await self.get_economic_calendar())

        await self.sendMessageTelegram('Events today : ' + str(len(self.__arrEconomicCalendar)) + '\n' + 'Events :')
        
        string_event = ''

        for x in self.__arrEconomicCalendar:
            
            string_event += self.str_format(x['time'],x['importance'],x['currency'],x['text'])
          
            if len(string_event) > 3900:
                await self.sendMessageTelegram(string_event)    
                string_event = ''

        await self.sendMessageTelegram(string_event)
            

        while True:
            for x in self.__arrEconomicCalendar:

                if self.check_times(x['time']):

                    string_event = self.str_format(x['time'],x['importance'],x['currency'],x['text'])
                    
                    self.__arrEconomicCalendar.remove(x)
                    await self.sendMessageTelegram(string_event)

            await asyncio.sleep(5)



async def main():
    ec = economicCalendar(CHAT_ID,TOKEN,LINK)
    task = asyncio.create_task(ec.loop())
    await asyncio.gather(task)



asyncio.run(main())

