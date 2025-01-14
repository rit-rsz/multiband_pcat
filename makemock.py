import numpy as np
from image_eval import image_model_eval, psf_poly_fit
import os
import sys

two_star_blend = 1
two_star_modes = ['r+i+g', 'rx3']
dim=29


np.random.seed(20170501)

#offsets = np.array([0.75], dtype=np.float32)
offsets = np.array([0.5,0.6, 0.75, 1.0, 1.2,1.5], dtype=np.float32)
flux_ratios = np.array([1.0, 2.0, 5.0], dtype=np.float32)
r_fluxes = np.array([250., 500., 1000.], dtype=np.float32)

class Mock:
    bands = ['r', 'i', 'g']
    #bands = ['r']
    nbands = len(bands)
    truebacks = [np.float32(179.) for x in xrange(nbands)]
    imsz = (dim, dim)
    nmgy_to_cts = 0.00546689
    gain = np.float32(4.62)
    n_realizations = 5
    same_flux = 1 # use this if you want multiple identical bands
    if sys.platform=='darwin':
        base_path = '/Users/richardfeder/Documents/multiband_pcat/pcat-lion-master'
    elif sys.platform=='linux2':
        base_path = '/n/fink1/rfeder/mpcat/multiband_pcat'

    dir_name = 'mock'+str(imsz[0])
    if two_star_blend:
    	dir_name = dir_name.replace('mock', 'mock_2star_')
        nstar = 2
    else:
        n_realizations = 1
    	nstar = int(0.15*imsz[0]**2)
        #nstar = 200
        print 'nstar:', nstar
    data_path = base_path+'/Data/'+dir_name
    #test for two sources of the same color
    #r_i_colors = [0, 0]
    #r_g_colors = [0, 0]

    r_i_colors = [0.3, 0.1]
    r_g_colors = [-0.5, -0.1]
    src_colors = [r_i_colors, r_g_colors]
    # normal mock dataset params
    truealpha = np.float32(2.0)
    trueminf = np.float32(236.)
    truelogf = np.random.exponential(scale=1./(truealpha-1.), size=nstar).astype(np.float32)
    if same_flux:
        normal_backs = np.array([179., 179., 179.],dtype=np.float32)
    else:
        normal_backs = np.array([179., 310., 115.], dtype=np.float32)
    
    n_second_pop = 0
    
    
    def make_mock_directories(self):
        dir_types = ['psfs', 'pixs', 'truth', 'cts']
        print self.data_path
        if not os.path.isdir(self.data_path):
            os.makedirs(self.data_path)
            for dir_type in dir_types:
                os.makedirs(self.data_path+'/'+dir_type)
                
    def mock_pix_psf_files(self, two_star_blend, two_star_mode):
        f = open(self.base_path+'/Data/sdss.0921/sdss.0921_psf.txt')
        nc, nbin = [np.int32(i) for i in f.readline().split()]
        f.close()
        psf = np.loadtxt(self.base_path+'/Data/sdss.0921/sdss.0921_psf.txt', skiprows=1).astype(np.float32)
        cf = psf_poly_fit(psf, nbin=nbin)
        
        nb = self.nbands
        if two_star_blend:
        	if two_star_mode=='rx3':
        		nb = 1
        for b in xrange(nb):
            f = open(self.data_path+'/pixs/'+self.dir_name+'-pix'+self.bands[b]+'.txt', 'w')
            if two_star_blend:
            	f.write('%1d\t%1d\t1\n0.\t%0.3f\n%0.8f\t%1d' % (self.imsz[0], self.imsz[1], self.gain, self.nmgy_to_cts, self.truebacks[b]))
            else:
            	f.write('%1d\t%1d\t1\n0.\t%0.3f\n%0.8f\t%1d' % (self.imsz[0], self.imsz[1], self.gain, self.nmgy_to_cts, self.normal_backs[b]))
            np.savetxt(self.data_path+'/psfs/'+self.dir_name+'-psf'+self.bands[b]+'.txt', psf, header='%1d\t%1d' % (nc, nbin), comments='')

        return nc, nbin, psf, cf
    def generate_noise_realizations(self):
        noise = np.zeros((self.nbands, self.n_realizations, self.imsz[0], self.imsz[1]), dtype=np.float32)
        for n in xrange(self.n_realizations):
            for b in xrange(self.nbands):
                noise[b,n] = np.random.normal(size=self.imsz).astype(np.float32)
                noise_path = self.data_path+'/noise'
                if not os.path.isdir(noise_path):
                    os.makedirs(noise_path)
                np.savetxt(noise_path+'/noise_band'+str(b)+'_nr'+str(n)+'.txt', noise[b,n])
        return noise
    

    def get_fluxes(self, flux, flux_ratio, two_star_mode):
        truefs = [np.zeros(self.nstar, dtype=np.float32) for x in xrange(self.nbands)]
        for b in xrange(self.nbands):
            if b==0:
                truefs[b][0] = flux
                truefs[b][1] = flux*flux_ratio
            else:
                truefs[b][0] = flux*10**(0.4*self.src_colors[b-1][0])
                truefs[b][1] = flux*flux_ratio*10**(0.4*self.src_colors[b-1][1])
        if two_star_mode=='rx3':
            truefs = [np.sum(np.array(truefs), axis=0)] # if coadd then just add fluxes from three bands together
        return truefs
    
    def get_positions(self, offset):
        truex = [self.imsz[0]/2, self.imsz[0]/2 + offset]
        truey = [self.imsz[1]/2, self.imsz[1]/2]
        return np.array(truex, dtype=np.float32), np.array(truey, dtype=np.float32)

    def make_mock_image(self, truex, truey, b, fluxes, nc, cf, noise, two_star_mode=None):
        mocks = []
        if two_star_mode is not None:
            mock0 = image_model_eval(truex, truey, fluxes[b], self.truebacks[b], self.imsz, nc, cf)
        else:
            mock0 = image_model_eval(truex, truey, fluxes[b], self.normal_backs[b], self.imsz, nc, cf)
        mock0[mock0 < 1] = 1.
        variance = mock0 / self.gain
        print np.mean(variance), np.std(variance)
        for n in xrange(self.n_realizations):
            # here is where I would put an if statement like
            # if two_star_mode == 'rx3':
            #     mock  = mock0 + (np.sqrt(variance)*np.mean(noise[:,n]))
            # i believe it would be the mean of the three since we already coadd the model image 
            # from which we calculate the variance.
            mock = mock0 + (np.sqrt(variance)*noise[b,n])
            mocks.append(mock)
        return mocks


def make_mock(offsets, flux_ratios, r_fluxes, dim, two_star_blend, two_star_modes):

	print 'Generating '+str(dim)+'x'+str(dim)+ ' mock dataset..'
	print 'two_star_blend =', two_star_blend
	if two_star_blend:
		print 'two_star_modes:', two_star_modes
                print 'offsets:', offsets
                print 'flux_ratios:', flux_ratios
                print 'r_fluxes:', r_fluxes

	x = Mock()
	x.make_mock_directories()
	noise = x.generate_noise_realizations()
        print len(noise)
	if two_star_blend:
		for two_star_mode in two_star_modes: # first r+i+g, then rx3
			print 'mode:', two_star_mode
        
			nc, nbin, psf, cf = x.mock_pix_psf_files(two_star_blend, two_star_mode)

			if two_star_mode=='rx3': # take sum of backgrounds, which are all the same in two star case
				x.truebacks = [x.truebacks[0]*3]
                                #x.truebacks = [x.truebacks[0]/3]
			for offset in offsets:
				truex, truey = x.get_positions(offset)
				for flux in r_fluxes:
					for flux_ratio in flux_ratios:
						truefs = x.get_fluxes(flux, flux_ratio, two_star_mode)
						f = flux
						nb = x.nbands
						if two_star_mode=='rx3':
                                                    # this technically not correct, but we don't use
                                                    # truth catalog to assess fractional flux error
                                                    f *= 3
                                                    nb = 1
						subdir = x.data_path+'/'+ x.dir_name+'-'+str(offset)+'-'+str(f)+'-'+str(flux_ratio)
						if not os.path.isdir(subdir):
							os.makedirs(subdir)
						truth = [truex, truey]
						for b in xrange(nb):
							mocks = x.make_mock_image(truex, truey, b, truefs, nc, cf, noise, two_star_mode)
							for n in xrange(x.n_realizations):
								np.savetxt(subdir+'/'+x.dir_name+'-'+str(offset)+'-'+str(f)+'-'+str(flux_ratio)+'-nr'+str(n+1)+'-cts'+x.bands[b]+'.txt', mocks[n])
							truth.append(truefs[b])
						truth = np.array(truth, dtype=np.float32).T
						np.savetxt(subdir+'/'+x.dir_name+'-'+str(offset)+'-'+str(f)+'-'+str(flux_ratio)+'-tru.txt', truth)
		print 'Files saved to ', x.data_path

	else: # NORMAL MOCK IMAGES 
		color_mus = [0.25, -0.25]
		color_sigs = [0.5, 0.5]
                #color_mus = [0.0, 0.0]
                #color_sigs = [0.001, 0.001]
		true_params = np.zeros(shape=(x.nstar, 2+x.nbands),dtype=np.float32)
		true_params[:,0] = np.random.uniform(size=x.nstar)*(x.imsz[0]-1) # x coordinate
		true_params[:,1] = np.random.uniform(size=x.nstar)*(x.imsz[1]-1) # y coordinate
		true_params[:,2] = x.trueminf * np.exp(x.truelogf) # r band flux

		# add other fluxes as needed
		for b in xrange(x.nbands-1):
                    if x.same_flux:
                        true_params[:,3+b] = true_params[:,2]
                    else:
                        colors = np.random.normal(loc=color_mus[b], scale=color_sigs[b], size=x.nstar-x.n_second_pop)
			colors = np.append(colors, np.random.normal(loc=-0.5, scale=0.1, size=x.n_second_pop))
			true_params[:,3+b] = true_params[:,2]*(10**(0.4*colors))
                        
		for b in xrange(x.nbands):
			nc, nbin, psf, cf = x.mock_pix_psf_files(0, 'x')


			mocks = x.make_mock_image(true_params[:,0], true_params[:,1], b, true_params[:,2:].T, nc, cf, noise)
                        #print len(mocks)
                        
                        #for n in xrange(x.n_realizations):
                        #    np.savetxt(x.data_path+'/cts/'+x.dir_name+'-cts'+str(x.bands[b])+'-nr'+str(n)+'.txt', mocks[n])
			np.savetxt(x.data_path+'/cts/'+x.dir_name+'-cts'+str(x.bands[b])+'.txt', mocks[0])
			#stack_mock = np.array(mocks[0])+np.array(mocks[1])+np.array(mocks[2])
                        #np.savetxt(x.data_path+'/cts/'+x.dir_name+'-cts'+str(x.bands[b])+'-stacked.txt', stack_mock) #stacked realizations
                        np.savetxt(x.data_path+'/psfs/'+x.dir_name+'-psf'+str(x.bands[b])+'.txt', psf, header='%1d\t%1d' % (nc, nbin), comments='')

			f = open(x.data_path+'/pixs/'+x.dir_name+'-pix'+str(x.bands[b])+'.txt', 'w')
			f.write('%1d\t%1d\t1\n0.\t%0.3f\n%0.8f\t%1d' % (x.imsz[0], x.imsz[1], x.gain, x.nmgy_to_cts, x.normal_backs[b]))
			f.close()
                        
		np.savetxt(x.data_path+'/truth/'+x.dir_name+'-tru.txt', true_params)



make_mock(offsets, flux_ratios, r_fluxes, dim, two_star_blend, two_star_modes)
