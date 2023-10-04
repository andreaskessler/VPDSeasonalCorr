import data
import data_defs
import seasons
import time

yMin = data.climateVars[0].yearMin_
yMax = data.climateVars[0].yearMax_
tstmp = time.strftime("%Y%m%d_%H%M%S")
for ps in data_defs.PS_VARS:
    out = open("heatmapdata_%s_%d_%d_%s.txt" % (ps, yMin, yMax, tstmp), "w")
    try:
        # Write header.
        out.write('Site')
        for s in seasons.Season.allMonths():
            out.write('\t%s' % s)
        out.write('\n')
        # Calc correlation.
        for site in data.milltree.siteNames_:
            out.write(site)
            cv = data.ClimatePS.getInstance(ps)
            assert cv, "%s for site %s" % (ps, site)
            print('.', end='', flush=True)
            for s in seasons.Season.allMonths():
                res_cor = 'NO DATA'
                if cv.year_[site]:
                    res_cor = cv.cor(site, s)
                out.write('\t%s' % res_cor)
            out.write('\n')
        print('.')
    finally:
        out.close()
print("calculation of heatmap correlations done.")


