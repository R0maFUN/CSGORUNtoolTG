from collections import deque
import requests
import datetime
import time

# make current-state request with proxy every 500ms
# get info from response:
# roundIds, roundKoefs
# if lastSavedRoundId < roundId -> process new round

# main class
#

bot_token = "1902397169:AAGGdJj-ydbS06ZLRebLT2PCJj6qj2O4Sy4"
bot_chatID = "@csgorun_stat"

class Round:
# members:
    m_id = 0
    m_koef = 0

# methods:
    def __init__(self, id, koef):
        m_id = id
        m_koef = koef

    def __str__(self):
        return "Round: #" + str(self.m_id) + " : " + str(self.m_koef)

class Statistics:
# members:
    m_lastRounds = deque(maxlen=15)
    m_lastRoundId = 0
    m_currentCrashRow = 0
    m_roundsAmount = 0

    m_soloBetweenDoubles = [0]
    m_doublesBetweenTriples = [0]
    m_triplesBetweenQuadros = [0]
    m_quadrosBetweenTriples = [0]

    m_count = {'solo' : 0, 'double' : 0, 'triple' : 0, 'quadro' : 0}
    m_lastTime = {'solo' : "", 'double' : "", 'triple' : "", 'quadro' : ""}
    m_roundsAfter = {'solo' : 0, 'double' : 0, 'triple' : 0, 'quadro' : 0}

# methods:
    def gotSolo(self):
        self.m_count['solo'] += 1
        self.m_lastTime['solo'] = datetime.datetime.now().strftime("%d-%m-%y %H:%M")
        self.m_roundsAfter['solo'] = 0
        self.m_soloBetweenDoubles[-1] += 1

    def gotDouble(self):
        self.m_count['double'] += 1
        self.m_lastTime['double'] = datetime.datetime.now().strftime("%d-%m-%y %H:%M")
        self.m_roundsAfter['double'] = 0
        self.m_soloBetweenDoubles.append(0)
        self.m_doublesBetweenTriples[-1] += 1

    def gotTriple(self):
        self.m_count['triple'] += 1
        self.m_lastTime['triple'] = datetime.datetime.now().strftime("%d-%m-%y %H:%M")
        self.m_roundsAfter['triple'] = 0
        self.m_soloBetweenDoubles.append(0)
        self.m_doublesBetweenTriples.append(0)
        self.m_doublesBetweenTriples[-1] += 1

    def gotQuadro(self):
        self.m_count['quadro'] += 1
        self.m_lastTime['quadro'] = datetime.datetime.now().strftime("%d-%m-%y %H:%M")
        self.m_roundsAfter['quadro'] = 0
        self.m_soloBetweenDoubles.append(0)
        self.m_doublesBetweenTriples.append(0)
        self.m_triplesBetweenQuadros.append(0)
        self.m_triplesBetweenQuadros[-1] += 1

    def processNewRound(self, round):
        if round.m_id <= self.m_lastRoundId:
            return

        if round.m_koef < 1.2:
            self.m_currentCrashRow += 1
        else:
            if self.m_currentCrashRow == 1:
                self.gotSolo()
            elif self.m_currentCrashRow == 2:
                self.gotDouble()
            elif self.m_currentCrashRow == 3:
                self.gotTriple()
            elif self.m_currentCrashRow > 3:
                self.gotQuadro()
            self.m_currentCrashRow = 0

        self.m_lastRoundId = round.m_id
        self.m_lastRounds.appendleft(round)
        self.m_roundsAmount += 1
        self.m_roundsAfter['double'] += 1
        self.m_roundsAfter['triple'] += 1
        self.m_roundsAfter['quadro'] += 1

    def getCurrentState(self):
        resp = requests.get('https://api.csgorun.pro/current-state?montaznayaPena=null')
        respJSON = resp.json()

        if resp.status_code != 200:
            return
        #print(respJSON)
        data = respJSON['data']
        lastRoundId = data['game']['history'][0]['id']
        lastRoundKoef = data['game']['history'][0]['crash']
        #print('got ID: ' + str(lastRoundId) + ' : ' + str(lastRoundKoef) + 'x')
        ret = Round(lastRoundId, lastRoundKoef)
        ret.m_id = lastRoundId
        ret.m_koef = lastRoundKoef
        return ret

    def getData(self):
        result = str()
        result += "R:" + str(self.m_lastRounds[0].m_id) + " : " + str(self.m_lastRounds[0].m_koef) + "x\n\n"
        result += "Solo between doubles:\n" + ", ".join(str(x) for x in self.m_soloBetweenDoubles) + "\n\n"
        result += "Doubles between triples:\n" + ", ".join(str(x) for x in self.m_doublesBetweenTriples) + "\n\n"
        result += "Triples between Quadros:\n" + ", ".join(str(x) for x in self.m_triplesBetweenQuadros) + "\n\n\n"

        result += "Total rounds: " + str(self.m_roundsAmount) + "\n\n"

        result += "Solo: " + str(self.m_count['solo']) + "\n\n"

        result += "Doubles: " + str(self.m_count['double']) + "\n"
        result += "Rounds after double: " + str(self.m_roundsAfter['double']) + "\n"
        result += "Last double time: " + str(self.m_lastTime['double']) + "\n\n"

        result += "Triples: " + str(self.m_count['triple']) + "\n"
        result += "Rounds after triple: " + str(self.m_roundsAfter['triple']) + "\n"
        result += "Last trple time: " + str(self.m_lastTime['triple']) + "\n\n"

        result += "Quadros: " + str(self.m_count['quadro']) + "\n"
        result += "Rounds after quadro: " + str(self.m_roundsAfter['quadro']) + "\n"
        result += "Last quadro time: " + str(self.m_lastTime['quadro']) + "\n\n"

        return result


    def telegram_bot_sendtext(self, bot_message):
        #print("bot_message = " + bot_message)
        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&text=' + self.getData()

        response = requests.get(send_text)

        return response.json()

    def startLoop(self):
        while(1):
            r = self.getCurrentState()
            #print("r.m_id = " + str(r.m_id) + " last: " + str(self.m_lastRoundId))
            if r.m_id > self.m_lastRoundId:

                self.processNewRound(r)
                print("new round id: " + r.m_id )
                #print(self.getData())

                self.telegram_bot_sendtext(self.getData())
                # send data to tg
            time.sleep(3)

if __name__ == '__main__':
    stats = Statistics()
    stats.startLoop()
