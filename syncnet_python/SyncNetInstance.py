#!/usr/bin/python
#-*- coding: utf-8 -*-


import torch
import numpy
import time, pdb, argparse, subprocess, os, math, glob
import cv2
import python_speech_features

from scipy import signal
from scipy.io import wavfile
from .SyncNetModel import *  
from shutil import rmtree
from device_config import DEVICE

# ==================== Get OFFSET ====================

def calc_pdist(feat1, feat2, vshift=10):
    win_size = vshift * 2 + 1
    feat2p = torch.nn.functional.pad(feat2, (0, 0, vshift, vshift))
    dists = []
    for i in range(len(feat1)):
        dists.append(torch.nn.functional.pairwise_distance(
            feat1[[i], :].repeat(win_size, 1),
            feat2p[i:i+win_size, :]
        ))
    return dists

# ==================== MAIN DEF ====================

class SyncNetInstance(torch.nn.Module):
    def __init__(self, dropout=0, num_layers_in_fc_layers=1024):
        super(SyncNetInstance, self).__init__()
        self.__S__ = S(num_layers_in_fc_layers=num_layers_in_fc_layers).to(DEVICE)
    
    def evaluate(self, opt, videofile):
        self.__S__.eval()

        tmp_ref_dir = os.path.join(opt.tmp_dir, opt.reference)
        if os.path.exists(tmp_ref_dir):
            rmtree(tmp_ref_dir)
        os.makedirs(tmp_ref_dir)

        command = ("ffmpeg -y -i %s -threads 1 -f image2 %s" % (
            videofile,
            os.path.join(tmp_ref_dir, '%06d.jpg')
        ))
        subprocess.call(command, shell=True, stdout=None)

        command = ("ffmpeg -y -i %s -async 1 -ac 1 -vn -acodec pcm_s16le -ar 16000 %s" % (
            videofile,
            os.path.join(tmp_ref_dir, 'audio.wav')
        ))
        subprocess.call(command, shell=True, stdout=None)
        
        images = []
        flist = glob.glob(os.path.join(tmp_ref_dir, '*.jpg'))
        flist.sort()
        for fname in flist:
            images.append(cv2.imread(fname))
        im = numpy.stack(images, axis=3)
        im = numpy.expand_dims(im, axis=0)
        im = numpy.transpose(im, (0, 3, 4, 1, 2))
        imtv = torch.from_numpy(im.astype('float32')).float().to(DEVICE)

        sample_rate, audio = wavfile.read(os.path.join(tmp_ref_dir, 'audio.wav'))
        mfcc = zip(*python_speech_features.mfcc(audio, sample_rate))
        mfcc = numpy.stack([numpy.array(i) for i in mfcc])
        cc = numpy.expand_dims(numpy.expand_dims(mfcc, axis=0), axis=0)
        cct = torch.from_numpy(cc.astype('float32')).float().to(DEVICE)

        if (float(len(audio)) / 16000) != (float(len(images)) / 25):
            print("WARNING: Audio (%.4fs) and video (%.4fs) lengths are different." % (
                float(len(audio)) / 16000,
                float(len(images)) / 25
            ))

        min_length = min(len(images), math.floor(len(audio) / 640))
        
        lastframe = min_length - 5
        im_feat = []
        cc_feat = []
        tS = time.time()
        for i in range(0, lastframe, opt.batch_size):
            im_batch = [ imtv[:, :, vframe:vframe+5, :, :] 
                         for vframe in range(i, min(lastframe, i+opt.batch_size)) ]
            im_in = torch.cat(im_batch, 0)
            im_in = im_in.to(DEVICE)
            im_out = self.__S__.forward_lip(im_in)
            im_feat.append(im_out.data.cpu())

            cc_batch = [ cct[:, :, :, vframe*4:vframe*4+20] 
                         for vframe in range(i, min(lastframe, i+opt.batch_size)) ]
            cc_in = torch.cat(cc_batch, 0)
            cc_in = cc_in.to(DEVICE)
            cc_out = self.__S__.forward_aud(cc_in)
            cc_feat.append(cc_out.data.cpu())

        im_feat = torch.cat(im_feat, 0)
        cc_feat = torch.cat(cc_feat, 0)

        print('Compute time %.3f sec.' % (time.time() - tS))

        dists = calc_pdist(im_feat, cc_feat, vshift=opt.vshift)
        mdist = torch.mean(torch.stack(dists, 1), 1)

        minval, minidx = torch.min(mdist, 0)
        offset = opt.vshift - minidx
        conf = torch.median(mdist) - minval

        fdist = numpy.stack([dist[minidx].numpy() for dist in dists])
        fconf = torch.median(mdist).numpy() - fdist
        fconfm = signal.medfilt(fconf, kernel_size=9)
        
        numpy.set_printoptions(formatter={'float': '{: 0.3f}'.format})
        print('Framewise conf: ')
        print(fconfm)
        print('AV offset: \t%d \nMin dist: \t%.3f\nConfidence: \t%.3f' % (offset, minval, conf))

        dists_npy = numpy.array([ dist.numpy() for dist in dists ])
        return offset.numpy(), conf.numpy(), dists_npy

    def extract_feature(self, opt, videofile):
        self.__S__.eval()
        
        cap = cv2.VideoCapture(videofile)
        images = []
        while True:
            ret, image = cap.read()
            if not ret:
                break
            images.append(image)
        im = numpy.stack(images, axis=3)
        im = numpy.expand_dims(im, axis=0)
        im = numpy.transpose(im, (0, 3, 4, 1, 2))
        imtv = torch.from_numpy(im.astype('float32')).float().to(DEVICE)
        
        lastframe = len(images) - 4
        im_feat = []
        tS = time.time()
        for i in range(0, lastframe, opt.batch_size):
            im_batch = [ imtv[:, :, vframe:vframe+5, :, :] 
                         for vframe in range(i, min(lastframe, i+opt.batch_size)) ]
            im_in = torch.cat(im_batch, 0).to(DEVICE)
            im_out = self.__S__.forward_lipfeat(im_in)
            im_feat.append(im_out.data.cpu())
        im_feat = torch.cat(im_feat, 0)

        print('Compute time %.3f sec.' % (time.time() - tS))
        return im_feat

    def loadParameters(self, path):
        loaded_state = torch.load(path, map_location=lambda storage, loc: storage)
        self_state = self.__S__.state_dict()
        for name, param in loaded_state.items():
            if name in self_state:
                self_state[name].copy_(param)
