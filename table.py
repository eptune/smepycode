import sqlite3
import numpy as np
import getelnum
import pdb
import uncertainties
from uncertainties import unumpy
import os
import postfit

def dump_stars(save=True,texcmd=False):
    conn = sqlite3.connect(os.environ['STARSDB'])
    cur = conn.cursor()

    elements = ['O','C']
    cuts={}
    texdict = {}
    cuts['C'] = postfit.globcut('C',table='t3')
    cuts['O'] = postfit.globcut('O',table='t2')


    cmd0 = """
SELECT
distinct(t1.name),t1.vmag,t1.d,t1.teff,t1.logg,t1.pop_flag,t1.monh,t1.ni_abund,
t2.o_nfits,t2.o_abund,t2.o_staterrlo,t2.o_staterrhi,
t3.c_nfits,t3.c_abund,t3.c_staterrlo,t3.c_staterrhi,
exo.name    

FROM 
mystars t1

LEFT JOIN
mystars t3 
ON
t1.id = t3.id AND (%s)

LEFT JOIN
mystars t2 
ON
t1.id = t2.id AND (%s)

LEFT JOIN
exo
ON
exo.oid = t1.oid

WHERE (%s) OR (%s)

ORDER BY 
t1.name
""" % (cuts['C'],cuts['O'],cuts['C'],cuts['O'])

    temptype = [('name','|S10'),('vmag',float),('d',int),('teff',int),
                ('logg',float),('pop_flag','|S10'),('monh',float),('ni_abund',float),
                ('o_nfits',float),('o_abund',float),('o_staterrlo',float),('o_staterrhi',float),
                ('c_nfits',float),('c_abund',float),('c_staterrlo',float),('c_staterrhi',float),
                ('exoname','|S10')]


    cur.execute(cmd0)
    out = cur.fetchall()#,dtype=temptype)

    out = np.array(out,dtype=temptype)
    outstr = []
    
    out['o_nfits'][np.where(np.isnan(out['o_nfits']))[0]]  = 0
    out['c_nfits'][np.where(np.isnan(out['c_nfits']))[0]]  = 0
    
    #subtract of solar abundance
    elements = ['O','C']
    abund,errhi,errlo,abndone,logeps = {},{},{},{},{}

    c2oarr = np.array([])
    for el in elements:
        p = getelnum.Getelnum(el)        
        elo = el.lower()
        abund[el] = out['%s_abund' % elo] - p.abnd_sol
        logeps[el] = out['%s_abund' % elo]
        errhi[el] = np.abs(out['%s_staterrlo' % elo])
        errlo[el] = out['%s_staterrhi' % elo]
    
    for i in range(len(out)):
        abundarr = np.array([abund['C'][i],abund['O'][i]])
        
        if np.isnan(abundarr).any():
            c2ostr = '$nan_{nan}^{+nan}$'
        else:
            for el in elements:
                cent = logeps[el][i]
                err = [errlo[el][i],errhi[el][i]]
                abndone[el] = unumpy.uarray(([cent,cent],err))

            c2o = 10**(abndone['C']-abndone['O'])
            c2ostr = '$%.2f_{-%.2f}^{+%.2f}$' % (c2o[0].nominal_value,c2o[0].std_dev(),c2o[1].std_dev() )
            c2oarr = np.append(c2oarr,c2o[0].nominal_value)

        o = out[i]

        planetstr = 'no'
        if o['exoname'] != 'None':
            planetstr = 'yes'

        #Indentation character
        a = '\\\[0ex] '
        
        #Global parameters for stars
        a += '%s & %.2f & %d & %d & '%(o['name'],o['vmag'],o['d'],o['teff'])
        a += '%.2f & %s & %s &'%(o['logg'],o['pop_flag'],planetstr)

        #Metalicity and Nickle abundances
        a += '%.2f & %.2f & '%(o['monh'],o['ni_abund'])
        
        #Oxygen
        a += '%d & $%.2f_{%.2f}^{+%.2f}$ & '%(o['o_nfits'],abund['O'][i],o['o_staterrlo'],o['o_staterrhi'])

        #Carbon
        a += '%d & $%.2f_{%.2f}^{+%.2f}$ & '%(o['c_nfits'],abund['C'][i],o['c_staterrlo'],o['c_staterrhi'])

        #The Ratio
        a += '%s \\\ \n ' % c2ostr

        a = a.replace('$nan_{nan}^{+nan}$',r'\nd')
        a = a.replace('None',r'\nd')
        a = a.replace('nan',r'\nd')

        outstr.append(a)

    
    c2ohist = np.histogram(c2oarr,bins = [0.,p.coThresh,1000.])[0]
    # Total number of c2o measurments
    texdict['nPlanetTot'] = len(np.where(out['exoname'] != 'None')[0])
    texdict['nStarsTot'] = len(out)
    texdict['ncoStarsTot'] = len(c2oarr)
    texdict['ncoLtThresh'],texdict['ncoGtThresh'] = tuple(c2ohist)
    texdict['coMin'],texdict['coMax'] = c2oarr.min(),c2oarr.max()

    if texcmd:
        return texdict

    if save:
        f = open('Thesis/tables/bigtable.tex','w')
        f.writelines(outstr)
