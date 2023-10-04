__monthsThisYear = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
__monthsLastYear = tuple(['p' + m for m in __monthsThisYear])
months = __monthsThisYear + __monthsLastYear

class Season(object):
    __instances = []
    __months = []
    __summer = None
    __hydroYear = None
    __year = None

    @staticmethod
    def __createAllSeasons(sI, eI):
        for s in range(sI, eI+1):
            for e in range(s, eI+1):
                o = Season(s, e)

    @staticmethod
    def allSeasons():
        if not Season.__instances:
            Season.__createAllSeasons(-10, 9)
        return Season.__instances

    @staticmethod
    def allMonths():
        if not Season.__months:
            Season.__createAllSeasons(-10, 9)
        return Season.__months

    @staticmethod
    def getSummer():
        if Season.__summer is None:
            Season.__summer = Season(months.index('Jun'), months.index('Aug'))
        return Season.__summer

    @staticmethod
    def getYear():
        if Season.__year is None:
            Season.__year = Season(months.index('Jan'), months.index('Dec'))
        return Season.__year

    @staticmethod
    def getHydroyear():
        if Season.__hydroYear is None:
            Season.__hydroYear = Season(months.index('pOct')-len(months), months.index('Sep'))
        return Season.__hydroYear

    def __init__(self, sI, eI):
        self.endI_ = eI
        self.startI_ = sI
        global months
        self.end_ = months[eI]
        self.start_ = months[sI]
        if not self in Season.__instances:
            Season.__instances.append(self)
            if sI == eI:
                Season.__months.append(self)
        self.__hash_ = Season.__instances.index(self)

    def __eq__(self, other):
        return self.startI_ == other.startI_ and self.endI_ == other.endI_

    def __hash__(self):
        return self.__hash_

    def __str__(self):
        desc = self.start_
        desc += '..'
        desc += self.end_
        #desc += '(%d,%d)' % (self.startI_, self.endI_)
        return desc

"""
def allSeasonsRec(sI, eI, res):
    #print("allSeasons(%d, %d, <%d>)" % (sI, eI, len(res)))
    if sI >= eI:
        return
    # Calculate maximal season.
    ses = []
    for i in range(sI, 0):
        ses.append(__monthsLastYear[i])
    for i in range(max(sI, 0), eI):
        ses.append(__monthsThisYear[i])
    # Abandon or add maximan season.
    if ses in res:
        return
    res.append(ses)
    # Recursion 1: shorten early.
    allSeasonsRec(sI+1, eI, res)
    # Recursion 2: shorten late.
    allSeasonsRec(sI, eI-1, res)
    return res
"""

if __name__ == '__main__':
    # Ad hoc module tests.
    print (len(Season.allSeasons()))
    s = Season(0,0)
    print (s)
    s = Season(5,7)
    print (s)
    s= Season(-10, 9)
    print (s)
    print (len(Season.allSeasons()))
    d = {}
    d[s] = 0

