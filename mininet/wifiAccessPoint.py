import os
import subprocess
import time
import socket
import struct
import fcntl
import fileinput

from mininet.wifiDevices import deviceDataRate

class accessPoint( object ):
    
    wpa_supplicantIsRunning = False

    def __init__( self, ap, country_code=None, auth_algs=None, wpa=None, intf=None, wlan=None,
              wpa_key_mgmt=None, rsn_pairwise=None, wpa_passphrase=None, encrypt=None, 
              wep_key0=None, **params ):

        if 'wlan' not in ap.params:
            newname = str(ap)+'-'+str('wlan')
            self.renameIface(intf, newname, wlan )
            self.getMacAddress(ap, wlan)
        self.start (ap, country_code, auth_algs, wpa, wlan,
              wpa_key_mgmt, rsn_pairwise, wpa_passphrase, encrypt, 
              wep_key0, **params)

    def renameIface( self, intf, newname, wlan ):
        "Rename interface"
        newname = str(newname) + str(wlan)
        os.system('ifconfig %s down' % intf)
        os.system('ip link set %s name %s' % (intf, newname))
        os.system('ifconfig %s up' % newname)                
    
    def start(self, ap, country_code=None, auth_algs=None, wpa=None, wlan=None,
              wpa_key_mgmt=None, rsn_pairwise=None, wpa_passphrase=None, encrypt=None, 
              wep_key0=None, **params):
        """ Starts an Access Point """
        
        self.cmd = ("echo \'")
        if 'wlan' not in ap.params:
            self.cmd = self.cmd + ("interface=%s-wlan%s" % (ap, wlan)) # the interface used by the AP
        else:
            wlan = ap.params.get('wlan')
            self.cmd = self.cmd + ("interface=%s" % wlan) # the interface used by the AP
        self.cmd = self.cmd + ("\ndriver=nl80211")
        self.cmd = self.cmd + ("\nssid=%s" % ap.ssid[0]) # the name of the AP
        
        
        if ap.params['mode'][0] == 'n' or ap.params['mode'][0] == 'ac'or ap.params['mode'][0] == 'a':
            self.cmd = self.cmd + ("\nhw_mode=g") 
        else:
            self.cmd = self.cmd + ("\nhw_mode=%s" % ap.params['mode'][0]) 
        self.cmd = self.cmd + ("\nchannel=%s" % ap.params['channel'][0]) # the channel to use 
        #if(ap.mode=="ac" or ap.mode=='a'):
        #   self.cmd = self.cmd + ("\nieee80211ac=1")
        self.cmd = self.cmd + ("\nwme_enabled=1") 
        self.cmd = self.cmd + ("\nwmm_enabled=1") 
        #if(ap.mode=="n" or ap.mode=="a"):
        #   self.cmd = self.cmd + ("\nieee80211n=1")
        #if(ap.mode=="n"):
        #   self.cmd = self.cmd + ("\nht_capab=[HT40+][SHORT-GI-40][DSSS_CCK-40]")        
        if encrypt == 'wpa':
            self.cmd = self.cmd + ("\nauth_algs=%s" % auth_algs)
            self.cmd = self.cmd + ("\nwpa=%s" % wpa)
            self.cmd = self.cmd + ("\nwpa_key_mgmt=%s" % wpa_key_mgmt ) 
            self.cmd = self.cmd + ("\nwpa_passphrase=%s" % wpa_passphrase)        
        elif encrypt == 'wpa2':
            self.cmd = self.cmd + ("\nauth_algs=%s" % auth_algs)
            self.cmd = self.cmd + ("\nwpa=%s" % wpa)
            self.cmd = self.cmd + ("\nwpa_key_mgmt=%s" % wpa_key_mgmt ) 
            self.cmd = self.cmd + ("\nrsn_pairwise=%s" % rsn_pairwise)  
            self.cmd = self.cmd + ("\nwpa_passphrase=%s" % wpa_passphrase)   
        elif encrypt == 'wep':
            self.cmd = self.cmd + ("\nauth_algs=%s" % auth_algs)
            self.cmd = self.cmd + ("\nwep_default_key=%s" % 0) 
            self.cmd = self.cmd + ("\nwep_key0=%s" % wep_key0)                         
                
        #Not used yet!
        if(country_code!=None):
            self.cmd = self.cmd + ("\ncountry_code=%s" % country_code) # the country code
        
        if(ap.n_ssids) > 1:
            i = 1
            while (int(ap.n_ssids) > i):
                self.cmd = self.cmd + ('\n')
                self.cmd = self.cmd + ("\nbss=%s-wlan%s_%s" % (ap, wlan, i))
                self.cmd = self.cmd + ("\nssid=%s_%s" % (ap.ssid[0], i))  
                i += 1 
            
        self.APfile(self.cmd, ap, wlan)   
  
    def getMacAddress(self, ap, wlan):
        """ get Mac Address of any Interface """
        iface = str(ap) + '-wlan' + str(wlan)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', '%s'[:15]) % iface)
        mac = (''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1])
        ap.params['mac'] = mac
        self.checkNetworkManager(mac)
        
    def checkNetworkManager(self, mac):
        """ add mac address inside of /etc/NetworkManager/NetworkManager.conf """
        self.printMac = False   
        unmatch = ""
        if(os.path.exists('/etc/NetworkManager/NetworkManager.conf')):
            if(os.path.isfile('/etc/NetworkManager/NetworkManager.conf')):
                self.resultIface = open('/etc/NetworkManager/NetworkManager.conf')
                lines=self.resultIface
        
            isNew=True
            for n in lines:
                if("unmanaged-devices" in n):
                    unmatch = n
                    echo = n
                    echo.replace(" ", "")
                    echo = echo[:-1]+";"
                    isNew = False
            if(isNew):
                os.system("echo '#' >> /etc/NetworkManager/NetworkManager.conf")
                unmatch = "#"
                echo = "[keyfile]\nunmanaged-devices="
            
            if mac not in unmatch:
                echo = echo + "mac:" + mac + ';'
                self.printMac = True
            
            if(self.printMac):
                for line in fileinput.input('/etc/NetworkManager/NetworkManager.conf', inplace=1): 
                    if(isNew):
                        if line.__contains__('#'): 
                            print line.replace(unmatch, echo)
                        else:
                            print line.rstrip()
                    else:
                        if line.__contains__('unmanaged-devices'): 
                            print line.replace(unmatch, echo)
                        else:
                            print line.rstrip()
                #necessary to add mac address before starting the ap
                time.sleep(2)
          
    @classmethod
    def apBridge(self, ap, iface):
        """ AP Bridge """  
        if 'wlan' not in ap.params:
            intf = str(ap)+'-'+'wlan'+str(iface)
            os.system("ovs-vsctl add-port %s %s" % (ap, intf))
        else:
            wlan = ap.params.get('wlan')
            os.system("ovs-vsctl add-port %s %s" % (ap, wlan))
       
    def setBw(self, ap, iface):
        """ Set bw to AP """ 
        value = deviceDataRate(ap, None, None)
        bw = value.rate
        
        ap.cmd("tc qdisc replace dev %s \
            root handle 2: tbf rate %sMbit burst 15000 latency 2ms" % (iface, bw))          
        #Reordering packets    
        ap.cmd('tc qdisc add dev %s parent 2:1 handle 10: pfifo limit 1000' % (iface))
        
    def APfile(self, cmd, ap, wlan):
        """ run an Access Point and create the config file  """
        if 'wlan' not in ap.params:
            wlan = str(ap) + '-wlan' + str(wlan)
        else:
            wlan = ap.params.get('wlan')
            os.system('ifconfig %s down' % wlan)
            os.system('ifconfig %s up' % wlan)
        content = cmd + ("\' > %s.conf" % wlan)  
        os.system(content)
        cmd = ("hostapd -B %s.conf" % wlan)
        subprocess.check_output(cmd, shell=True)
        self.setBw(ap, wlan)