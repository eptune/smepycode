import idlsave
import numpy as np
import matplotlib.pyplot as plt
import savunpack
import matplotlib.mlab as mlab


class ReadStars:
    def __init__(self,starsfile,var='stars'):
        junk = idlsave.read(starsfile)
        self.stars = junk[var]
        self.star = self.stars[0]
        self.fields = np.array(self.stars.dtype.names)
        
        #make fields lowercase
        for i in range(len(self.fields)):
            self.fields[i] = self.fields[i].lower()

        #assign attributes to class
        for field in self.fields:
            if type(self.star[field]) is np.ndarray:
                unpackedfield = savunpack.savunpack(self.stars[field])
                exec('self.'+field+' = unpackedfield')
            else:
                exec('self.'+field+' = self.stars["'+field+'"]')

