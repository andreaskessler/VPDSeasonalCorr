import data
import seasons
import time

corr = {} # Key: site value: dict(key: var value: dict(key: season value: correlation)) 

yMin = data.climateVars[0].yearMin_
yMax = data.climateVars[0].yearMax_
tstmp = time.strftime("%Y%m%d_%H%M%S")
out = open("out_%d_%d_%s.txt" % (yMin, yMax, tstmp), "w")
try:
    fmt = '%s\t%s\t%s\t%s\t%s\t%s\n'
    out.write(fmt % ('Site', 'Var', 'YearFrom', 'YearTo', 'Season', 'Cor'))
    for site in data.milltree.data_.keys():
        corr[site] = {}
        print(site, end='')
        for cv in data.climateVars:
            corr[site][cv.var_] = {}
            print('.', end='', flush=True)
            for s in seasons.Season.allSeasons():
                res_cor = 'NO DATA'
                y_from = '-'
                y_to = '-'
                if cv.year_[site]:
                    y_from = cv.year_[site][0]
                    y_to = cv.year_[site][-1]
                    res_cor = cv.cor(site, s)
                    #print('%s: %s %s(%d..%d) vs. %s' % (s, site, cv.var_, cv.year_[site][0], cv.year_[site][-1], data.milltree))
                out.write(fmt % (site, cv.var_, y_from, y_to, s, res_cor))
                corr[site][cv.var_][s] = res_cor
        print('.')
finally:
    out.close()
print("calculation of correlations done.")

out = open("summary_%d_%d_%s.txt" % (yMin, yMax, tstmp), "w")
try:
    # Define standard season
    ss = seasons.Season(5,7)

    # Prepare headers.
    fmt1 = '%s\t%s\t%s\t%s'
    out.write(fmt1 % ('Site', 'VarMaxPos', 'Season', 'r'))
    fmt2 = '\t%s\t%s\t%s'
    out.write(fmt2 % ('VarMaxNeg', 'Season', 'r'))
    fmt3 = '\t%s\t%s\t%s'
    for cv in data.climateVars:
           out.write(fmt3 % ('%sMax Season' % (cv.var_),
                             '%s r' % (cv.var_),
                             '%s %s r' % (cv.var_, ss)))
    out.write("\n")

    # Loop over sites.
    for site in corr.keys():
        # Find min and max per site.
        max_var =None
        max_s = None
        max_r = -1
        min_var = None
        min_s = None
        min_r = 1
        for cvn in corr[site].keys():
            for s, r in corr[site][cvn].items():
                try:
                    r = float(r)
                except:
                    continue
                if r > max_r:
                    max_var = cvn
                    max_s = s
                    max_r = r
                if r < min_r:
                    min_var = cvn
                    min_s = s
                    min_r = r
        out.write(fmt1 % (site, max_var, max_s, max_r))
        out.write(fmt2 % (min_var, min_s, min_r))
        # Find max per var.
        for cvn in corr[site].keys():
            max_s = None
            max_r = 0
            ss_r = None
            for s, r in corr[site][cvn].items():
                try:
                    r = float(r)
                except:
                    continue
                if abs(r) > abs(max_r):
                    max_s = s
                    max_r = r
                if s == ss:
                   ss_r = r
            out.write(fmt3 % (max_s, max_r, ss_r))
        out.write('\n')
finally:
    out.close()
print("summary done.")
