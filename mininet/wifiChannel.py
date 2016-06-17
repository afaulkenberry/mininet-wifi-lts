"""
author: Ramon Fontes (ramonrf@dca.fee.unicamp.br)
"""

from wifiDevices import deviceDataRate
from wifiPropagationModels import propagationModel_
from scipy.spatial.distance import pdist
import numpy as np
import math
import random

class channelParameters ( object ):
    """Channel Parameters""" 
    
    delay = 0
    loss = 0
    bw = 0
    latency = 0
    rate = 0
    dist = 0
    noise = 0
    i = 0
    sl = 1 #System Loss
    lF = 0 #Floor penetration loss factor
    nFloors = 0 #Number of floors
    gRandom = 0 #Gaussian random variable
    
    def __init__( self, node1, node2, wlan, dist, staList, time ):
        self.dist = dist
        #self.calculateInterference(node1, node2, dist, staList, wlan)    
        self.delay = self.delay(self.dist, time)
        self.latency = self.latency(self.dist)
        self.loss = self.loss(self.dist)
        self.bw = self.bw(node1, node2, self.dist, wlan)
        self.tc(node1, wlan, self.bw, self.loss, self.latency, self.delay)        
        
    @classmethod
    def getDistance(self, src, dst):
        """ Get the distance between two nodes """
        pos_src = src.params['position']
        pos_dst = dst.params['position']
        points = np.array([(pos_src[0], pos_src[1], pos_src[2]), (pos_dst[0], pos_dst[1], pos_dst[2])])
        dist = pdist(points)
        return float(dist)
            
    def delay(self, dist, time):
        """"Based on RandomPropagationDelayModel"""
        if time != 0:
            self.delay = dist/time
        else:
            self.delay = dist/10
        return self.delay   
    
    def latency(self, dist):    
        self.latency = 2 + dist
        return self.latency
        
    def loss(self, dist):  
        if dist!=0:
            self.loss =  abs(math.log10(dist * dist))
        else:
            self.loss = 0.1
        return self.loss
    
    def bw(self, sta, ap, dist, wlan):
        self.rate = 0
        if propagationModel_.model == '':
            propagationModel_.model = 'friisPropagationLossModel'
        value = deviceDataRate(sta, ap, wlan)
        custombw = value.rate
        self.rate = value.rate/2.5
        lF = self.lF     
        sl = self.sl
        nFloors = self.nFloors
        gRandom = self.gRandom
        if ap == None:
            gT = 0
            hT = 0
            pT = sta.params['txpower'][wlan]
            gR = sta.params['antennaGain'][wlan]
            hR = sta.params['antennaHeight'][wlan]            
            if self.i != 0:
                dist = self.dist/self.i
            value = propagationModel_( sta, ap, dist, wlan, pT, gT, gR, hT, hR, sl, lF, nFloors, gRandom)
            sta.params['rssi'][wlan] = value.rssi # random.uniform(value.rssi-1, value.rssi+1)
            self.rate = (custombw * (1.1 ** -dist))/5
        else:            
            pT = ap.params['txpower'][0]
            gT = ap.params['antennaGain'][0]
            hT = ap.params['antennaHeight'][0]
            gR = sta.params['antennaGain'][wlan]
            hR = sta.params['antennaHeight'][wlan]       
            value = propagationModel_( sta, ap, dist, wlan, pT, gT, gR, hT, hR, sl, lF, nFloors, gRandom)
            sta.params['rssi'][wlan] = value.rssi #random.uniform(value.rssi-1, value.rssi+1)
            if ap.equipmentModel == None:
                self.rate = custombw * (1.1 ** -dist)
        self.rate = self.rate - self.loss*3
        if self.rate <= 0:
            self.rate = 1
        return self.rate  
    
    @classmethod
    def tc(self, sta, wlan, bw, loss, latency, delay):
        """Applying TC"""
        bw = abs(random.uniform(bw-0.5, bw+0.5))        
        
        sta.pexec("tc qdisc replace dev %s \
            root handle 2: netem rate %.2fmbit \
            loss %.1f%% \
            latency %.2fms \
            delay %.2fms \
            corrupt 0.1%%" % (sta.params['wlan'][wlan], bw, loss, latency, delay))
        
    def calculateInterference (self, sta, ap, dist, staList, wlan):      
        """Calculating Interference"""
        self.noise = 0
        noisePower = 0
        self.i=0
        signalPower = sta.params['rssi'][wlan]    
        
        if ap == None:
            for station in staList:
                if station != sta and sta.params['associatedTo'][wlan] != '':
                    self.calculateNoise(sta, station, signalPower, wlan)
        else:
            for station in ap.associatedStations:
                if station != sta and sta.params['associatedTo'][wlan] != '':
                    self.calculateNoise(sta, station, signalPower, wlan)
        if self.noise != 0:
            noisePower = self.noise/self.i
            self.dist = self.dist + dist
            signalPower = sta.params['rssi'][wlan]
            snr = self.signalToNoiseRatio(signalPower, noisePower)
            sta.params['snr'][wlan] = random.uniform(snr-1, snr+1)
        else:
            sta.params['snr'][wlan] = 0
            
    def calculateNoise(self, sta, station, signalPower, wlan):
        dist = self.getDistance(sta, station)
        totalRange = sta.range + station.range
        if dist < totalRange:
            value = propagationModel_(sta, station, dist, wlan)
            n =  value.rssi + signalPower
            self.noise += n
            self.i+=1    
            self.dist += dist  
            
    @classmethod        
    def frequency(self, node, wlan):
        freq = 0
        if node.params['channel'][wlan] == 1:
            freq = 2.412
        elif node.params['channel'][wlan] == 2:
            freq = 2.417
        elif node.params['channel'][wlan] == 3:
            freq = 2.422
        elif node.params['channel'][wlan] == 4:
            freq = 2.427
        elif node.params['channel'][wlan] == 5:
            freq = 2.432
        elif node.params['channel'][wlan] == 6:
            freq = 2.437
        elif node.params['channel'][wlan] == 7:
            freq = 2.442
        elif node.params['channel'][wlan] == 8:
            freq = 2.447
        elif node.params['channel'][wlan] == 9:
            freq = 2.452
        elif node.params['channel'][wlan] == 10:
            freq = 2.457
        elif node.params['channel'][wlan] == 11:
            freq = 2.462
        return freq
            
    def signalToNoiseRatio(self, signalPower, noisePower):    
        """Calculating SNR margin"""
        snr = signalPower - noisePower
        return snr

    def maxChannelNoise(self, node1, node2, wlan, modelValue):  
        """Have to work"""  
        #snr = 25 #Depends of the equipment
        #max_channel_noise = self.rssi[wlan] - snr
        
    def linkMargin(self, node1, node2, wlan, modelValue):    
        """Have to work"""
        #receive_sensitivity = -72 #Depends of the equipment
        #link_margin = self.rssi[wlan] - receive_sensitivity