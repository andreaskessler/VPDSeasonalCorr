import glob
import math
import rpy2
import rpy2.robjects

cor_test = rpy2.robjects.r['cor.test']
FloatVector = rpy2.robjects.vectors.FloatVector
# res = cor_test(FloatVector(a),FloatVector(b))
# res = rpy2.robjects.r.cor(FloatVector(a),FloatVector(b))

import data_defs

YEAR_MIN=data_defs.YEAR_MIN
YEAR_MAX=data_defs.YEAR_MAX

OP_MEAN = 'Mean'
OP_MEANSUM = 'MeanSum'

class ClimatePS(object):
    # CRU TS = Climatic Research Unit Timeseries
    # Preprocessed format to contain our sites.
    # Format:
    # Filename: CRU_<var>_18Osites_<y0>_<y1>.txt
    # Header: site-codes
    # Data:
    #        y0_m1
    #        y0_m2
    #        ...
    #        y0_m12
    #        ...
    #        y1_m12
    __instances = []

    @staticmethod
    def getInstance(var):
        i = None
        for c in ClimatePS.__instances:
            if c.var_ == var:
                i = c
                break
        return i
    
    def __init__(self, var, yearMin=1920, yearMax=2000, loadFile=True):
        self.sep_ = '\t'
        self.var_ = var
        self.yearMin_ = yearMin
        self.yearMax_ = yearMax
        self.dataM_ = {} # key: site-name value: [monthly value array]
        self.year_ = {} # key: site-name value: [years]
        if loadFile:
            self.filename_ = self.__findFile()
            self.year0_ = int(self.filename_[-13:-9])
            self.year1_ = int(self.filename_[-8:-4])
            assert self.__loadFile(self.filename_)
            print(self.describe())
        else:
            self.filename_ = 'No file'
            self.year0_ = 0
            self.year1_ = 0
        if not self in ClimatePS.__instances:
            ClimatePS.__instances.append(self)
        # Yearly data as seasonal avarage are lazy calculated:
        self.data_ = {}  # key: site-name value: {key: season value: [values]}
        self.dataMinMax_ = None

    def __getMinMax(self):
        if self.dataM_ and self.dataMinMax_ is None:
            mi = 1e99
            ma = -1e99
            for s in self.dataM_:
                mi = min(mi, min(self.dataM_[s]))
                ma = max(ma, max(self.dataM_[s]))
            self.dataMinMax_ = (mi, ma)
        return self.dataMinMax_

    def __eq__(self, other):
        return self.var_ == other.var_
   
    def __findFile(self):
        p = 'data/CRU_%s_18Osites_*_*.txt' % self.var_
        l = glob.glob(p)
        assert len(l) == 1, 'CRU data file for %s not unique' % self.var_
        return l[0]

    def __loadFile(self, fileName):
        res = False
        self.dataM_.clear()
        f = open(fileName, 'r')
        try:
            headers = f.readline().strip().split(self.sep_)
            sites = headers
            for site in sites:
                self.dataM_[site] = []
                self.year_[site] = []
            c = 0
            year = self.year0_ - 1
            line = f.readline()
            while line:
                c += 1
                if c % 12 == 1:
                    # New year starts.
                    for site in self.dataM_.keys():
                        sd = self.dataM_[site]
                        if sd and year <= self.yearMax_:
                            self.year_[site].append(year)
                    year += 1
                if year >= self.yearMin_ and year <= self.yearMax_:
                    line = line.strip()
                    tokens = line.split(self.sep_)
                    i = 0
                    for vStr in tokens:
                        try:
                            v = float(vStr)
                            self.dataM_[sites[i]].append(v)
                        except:
                            pass
                        i += 1
                line = f.readline()
            # No data for previous year?
            for site in self.dataM_.keys():
                sd = self.dataM_[site]
                if sd and year <= self.yearMax_:
                    self.year_[site].append(year)
            res = (c == 12 * (self.year1_ - self.year0_ + 1))
        finally:
            f.close()
        return res

    def calcStat(self, op, site, season):
        if op == OP_MEAN:
            a = self.__getVector(site, season)
            params = {'na.rm' : True}
            res = rpy2.robjects.r.mean(a, **params)
            #print ("mean(%s)=%s" % (a.r_repr(),res.r_repr()))
            return float(res[0])
        elif op == OP_MEANSUM:
            a = self.__calcSum(site, season)
            a = FloatVector(a)
            params = {'na.rm' : True}
            res = rpy2.robjects.r.mean(a, **params)
            return float(res[0])
        #    return self.()
        raise Exception('operations %s not implemented' % op)

    def modelQuotient(self, other, p1, p2, standardize=False):
        if self.var_ != 'precip' and other.var_ != 'VPD':
            assert False, "model quotient undefined"
        if self.yearMin_ != other.yearMin_ or self.yearMax_ != other.yearMax_:
            assert False, "different year boundaries not implemented"
        if self.year0_ != other.year0_ or self.year1_ != other.year1_:
            assert False, "different year data not implemented"
        preff = ''
        if standardize:
            preff = 'stand_'
        res = ClimatePS('%s%g_preicp_div_%g_VPD' % (preff, p1, p2), loadFile=False)
        res.year0_ = self.year0_
        res.year1_ = self.year1_
        if standardize:
            smi, sma = self.__getMinMax()
            omi, oma = other.__getMinMax()
        for s in self.year_:
            if self.year_[s] != other.year_[s]:
                # No data, else abort.
                if not self.year_[s]:
                    res.dataM_[s] = self.dataM_[s]
                elif not other.year_[s]:
                    res.dataM_[s] = other.dataM_[s]
                else:
                    assert False, "different year ranges not implemented"
                res.year_[s] = []
            else:
                res.year_[s] = self.year_[s]
                # Calc new series as difference.
                assert len(self.dataM_[s] ) == len(other.dataM_[s])
                a = self.dataM_[s]
                b = other.dataM_[s]
                if standardize:
                    a = [(x - smi)/(sma-smi) for x in a]
                    b = [(x - omi)/(oma-omi) for x in b]
                modelvals =list(a)
                for i in range(len(modelvals)):
                    modelvals[i] *= p1
                    modelvals[i] /= p2 * b[i]
                    # no, division by zero:
                    #modelvals[i] = 1/(p1*modelvals[i])
                    #modelvals[i] *= p2 * b[i]
                res.dataM_[s] = modelvals
        return res

    def modelProduct(self, other, p1, p2, standardize=False):
        if self.var_ != 'precip' and other.var_ != 'VPD':
            assert False, "model quotient undefined"
        if self.yearMin_ != other.yearMin_ or self.yearMax_ != other.yearMax_:
            assert False, "different year boundaries not implemented"
        if self.year0_ != other.year0_ or self.year1_ != other.year1_:
            assert False, "different year data not implemented"
        preff = ''
        if standardize:
            preff = 'stand_'
        res = ClimatePS('%s%g_preicp_mult_%g_VPD' % (preff, p1, p2), loadFile=False)
        res.year0_ = self.year0_
        res.year1_ = self.year1_
        if standardize:
            smi, sma = self.__getMinMax()
            omi, oma = other.__getMinMax()
        for s in self.year_:
            if self.year_[s] != other.year_[s]:
                # No data, else abort.
                if not self.year_[s]:
                    res.dataM_[s] = self.dataM_[s]
                elif not other.year_[s]:
                    res.dataM_[s] = other.dataM_[s]
                else:
                    assert False, "different year ranges not implemented"
                res.year_[s] = []
            else:
                res.year_[s] = self.year_[s]
                # Calc new series as difference.
                assert len(self.dataM_[s] ) == len(other.dataM_[s])
                a = self.dataM_[s]
                b = other.dataM_[s]
                if standardize:
                    a = [(x - smi)/(sma-smi) for x in a]
                    b = [(x - omi)/(oma-omi) for x in b]
                modelvals =list(a)
                for i in range(len(modelvals)):
                    modelvals[i] *= p1
                    modelvals[i] *= p2 * b[i]
                res.dataM_[s] = modelvals
        return res

    def modelSum(self, other, p1, p2, standardize=False):
        if self.var_ != 'precip' and other.var_ != 'VPD':
            assert False, "model sum undefined"
        if self.yearMin_ != other.yearMin_ or self.yearMax_ != other.yearMax_:
            assert False, "different year boundaries not implemented"
        if self.year0_ != other.year0_ or self.year1_ != other.year1_:
            assert False, "different year data not implemented"
        preff = ''
        if standardize:
            preff = 'stand_'
        res = ClimatePS('%s%g_preicp_plus_%g_VPD' % (preff, p1, p2), loadFile=False)
        res.year0_ = self.year0_
        res.year1_ = self.year1_
        if standardize:
            smi, sma = self.__getMinMax()
            omi, oma = other.__getMinMax()
        for s in self.year_:
            if self.year_[s] != other.year_[s]:
                # No data, else abort.
                if not self.year_[s]:
                    res.dataM_[s] = self.dataM_[s]
                elif not other.year_[s]:
                    res.dataM_[s] = other.dataM_[s]
                else:
                    assert False, "different year ranges not implemented"
                res.year_[s] = []
            else:
                res.year_[s] = self.year_[s]
                # Calc new series as difference.
                assert len(self.dataM_[s] ) == len(other.dataM_[s])
                a = self.dataM_[s]
                b = other.dataM_[s]
                if standardize:
                    a = [(x - smi)/(sma-smi) for x in a]
                    b = [(x - omi)/(oma-omi) for x in b]
                modelvals =list(a)
                for i in range(len(modelvals)):
                    modelvals[i] *= p1
                    modelvals[i] += p2 * b[i]
                res.dataM_[s] = modelvals
        return res
        
    def __sub__(self, other):
        if self.var_ != 'precip' and other.var_ != 'PET':
            assert False, "subtraction undefined"
        if self.yearMin_ != other.yearMin_ or self.yearMax_ != other.yearMax_:
            assert False, "different year boundaries not implemented"
        if self.year0_ != other.year0_ or self.year1_ != other.year1_:
            assert False, "different year data not implemented"
        res = ClimatePS('WAB', loadFile=False)
        res.year0_ = self.year0_
        res.year1_ = self.year1_
        for s in self.year_:
            if not s in other.year_:
                print("Warning: site %s missing in %s, WAB will not be available" % (
                    s, other.var_))
                continue
            if self.year_[s] != other.year_[s]:
                # No data, else abort.
                if not self.year_[s]:
                    res.dataM_[s] = self.dataM_[s]
                elif not other.year_[s]:
                    res.dataM_[s] = other.dataM_[s]
                else:
                    assert False, "different year ranges not implemented"
                res.year_[s] = []
            else:
                res.year_[s] = self.year_[s]
                # Calc new series as difference.
                assert len(self.dataM_[s] ) == len(other.dataM_[s])
                a = self.dataM_[s]
                b = other.dataM_[s]
                amb =list(a)
                for i in range(len(amb)):
                    amb[i] -= b[i]
                res.dataM_[s] = amb
        return res
        
    def describe(self):
        desc = ''
        desc += 'File:%s\n' % self.filename_
        desc += '%d sites\n' % len(self.dataM_)
        c = 0
        for ds in self.dataM_.values():
            c += len(ds)
        desc += '%d points between %d and %d\n' % (c, self.year0_, self.year1_)
        return desc

    def __str__(self):
        return self.var_

    def __calcAvg(self, site, season):
        # Calc seasonal average (mean).
        #debug = site=='Col'
        res = []
        i = 0
        series = self.dataM_[site]
        #if debug: print("__calcAvg(%s, %s)" % (site, season))
        #if debug: print("  series=[%s..%s]" % (series[:5], series[-5:]))
        while i < len(self.year_[site]):
            a = math.nan
            sI = i * 12 + season.startI_
            eI = i * 12 + season.endI_
            if sI >= 0 and sI < len(series) and eI >= 0 and eI < len(series):
                a = sum(series[sI:(eI+1)])
                a /= eI - sI + 1
            res.append(a)
            #if debug: print("  %d: sI=%d eI=%d -> append(%s)" % (i, sI, eI, a))
            i += 1
        return res

    def __calcSum(self, site, season):
        # Calc seasonal sum.
        res = []
        i = 0
        series = self.dataM_[site]
        while i < len(self.year_[site]):
            a = math.nan
            sI = i * 12 + season.startI_
            eI = i * 12 + season.endI_
            if sI >= 0 and sI < len(series) and eI >= 0 and eI < len(series):
                a = sum(series[sI:(eI+1)])
            res.append(a)
            i += 1
        return res
    
    def cor(self, site, season):
        a = self.__getVector(site, season)
        b = milltree.getVector(site, self.year_[site][0], self.year_[site][-1])
        #print ("cor(%s,%s) %d...%d" % (len(a),len(b), self.year_[site][0], self.year_[site][-1]))
        res = rpy2.robjects.r.cor(a, b, use="na.or.complete")
        #print ("cor(%s,%s)=%s" % (a,b,res.r_repr()))
        return float(res[0])

    def __getVector(self, site, season):
        if site not in self.data_:
            self.data_[site] = {}
        if season not in self.data_[site]:
            # Calc seasonal average.
            self.data_[site][season] = self.__calcAvg(site, season)
            #print("data[%s][%s]:=%s" % (site, season, self.data_[site][season]))
        d = self.data_[site][season]
        y = self.year_[site]
        assert len(d) == len(y)
        b = FloatVector(d)
        return b    

class Milltree(object):
    def __init__(self):
        self.sep_ = '\t'
        self.filename_ = data_defs.FILE_PATH_18O
        self.siteNames_ = data_defs.SITE_NAMES
        self.data_ = {} # key: site-name value: [values]
        self.year_ = {} # key: site-name value: [years]
        assert self.__loadFile(self.filename_)
        print(self.describe())

    def getVector(self, site, fromYear, toYear):
        l = self.year_[site]
        if toYear >= l[-1]:
            v = self.data_[site][l.index(fromYear):]
            for i in range(l[-1]+1, toYear + 1):
                v.append(math.nan)
        else:
            v = self.data_[site][l.index(fromYear):l.index(toYear)+1]
        assert len(v) == toYear - fromYear + 1, "%d to %d: len(v) = %d" % (fromYear, toYear, len(v))
        return FloatVector(v)


    def __loadFile(self, fileName):
        # Format:
        # year	Site1	Site2
        # 1900  0.4     0.7
        # 1901  0.42    0.68
        #
        res = False
        self.data_.clear()
        f = open(fileName, 'r')
        try:
            headers = f.readline().strip().split(self.sep_)
            assert headers[0] == 'year', 'unexpected file format'
            sites = headers[1:]
            if not self.siteNames_:
                self.siteNames_ = sites
            for site in self.siteNames_:
                self.data_[site] = []
                self.year_[site] = []
            line = f.readline()
            while line:
                tokens = line.split(self.sep_)
                year = int(tokens[0])
                i = 0
                for vStr in tokens[1:]:
                    try:
                        v = float(vStr)
                        self.data_[sites[i]].append(v)
                        self.year_[sites[i]].append(year)
                    except:
                        pass
                    i += 1
                line = f.readline()
            res = True     
        finally:
            f.close()
        if res:
            for site in self.data_.keys():
                assert len(self.data_[site]) == len(self.year_[site])
        return res

    def describe(self):
        desc = ''
        desc += 'File:%s\n' % self.filename_
        desc += '%d sites\n' % len(self.data_)
        for site in self.data_.keys():
            desc += site
            desc += ' '
        desc += '\n'
        c = 0
        ymin = 3000
        ymax = 0
        for ys in self.year_.values():
            c += len(ys)
            ymin = min(ymin, ys[0])
            ymax = max(ymax, ys[-1])
        desc += '%d points between %d and %d\n' % (c, ymin, ymax)
        return desc

    def __str__(self):
        return self.filename_

milltree = Milltree()
climateVars = (ClimatePS('VPD', yearMin=YEAR_MIN, yearMax=YEAR_MAX),
               ClimatePS('SPEI', yearMin=YEAR_MIN, yearMax=YEAR_MAX),
               ClimatePS('PET', yearMin=YEAR_MIN, yearMax=YEAR_MAX) ,
               ClimatePS('precip', yearMin=YEAR_MIN, yearMax=YEAR_MAX), 
               ClimatePS('Tmax', yearMin=YEAR_MIN, yearMax=YEAR_MAX),
               ClimatePS('Tmean', yearMin=YEAR_MIN, yearMax=YEAR_MAX),
               ClimatePS('Tmin', yearMin=YEAR_MIN, yearMax=YEAR_MAX),
               ClimatePS('vaporpressure', yearMin=YEAR_MIN, yearMax=YEAR_MAX),
               ClimatePS('wetdays', yearMin=YEAR_MIN, yearMax=YEAR_MAX),
               ClimatePS.getInstance('precip')-ClimatePS.getInstance('PET'),
)

if __name__ == '__main__':
    # Ad hoc module tests.
    d = ClimatePS('PET')
    print(d.dataM_['For'])
    print(d.year_['For'])
    print(d.dataM_['Tor'])
    print(d.year_['Tor'])
