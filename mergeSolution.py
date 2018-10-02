#!/usr/bin/python
import xmlrpclib
import os
import datetime
import time

SATELLITE_URL = "https://spacewalk.nchosting.dk/rpc/api"
SATELLITE_LOGIN = os.environ.get('SATELITE_USERNAME', 'linux-patchmangement')
SATELLITE_PASSWORD = os.environ.get('SATELITE_PASSWORD', 'q4jfFchaevhsR2zk')

client = xmlrpclib.Server(SATELLITE_URL, verbose=0)
key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)


patchchannels = ["spd-patch-channel",
                 "spt-patch-channel",
                 "spp-patch-channel"]


subchannels = ["netc_el7_epel",
               "netc_el7_jenkins",
               "netc_el7_jpackage6",
               "netc_el7_puppet-deps",
               "netc_el7_spacewalk27_client",
               "netc_ol7_latest",
               "netc_ol7_optional_latest",
               "netc_ol7_uekr4_latest"]

testchannels = ["netc_el7_elasticsearch_kibana-4.5", "netc_el7_vmware"]

########################################################################################################################
def getFileLine(file):
  a = []
  with open(file, "r") as file:
    for line in file:
      a.append(line.rstrip())
  return a

def f_str(set):
 longest = 0
 for i in set:
  curr = len(str(i))
  if curr > longest:
   longest = curr
 return longest

########################################################################################################################
# Get all child channels from a given basechannel.
def getChildChannels(regex):
 channels = set()
 get = client.channel.software.listChildren(key, regex)
 for i in range(len(get)):
  channels.add(get[i]['label'])
 return channels

########################################################################################################################
def createPatchChannels(channels, packages):

 rootchannel = ""
 list = []
 substruc = client.channel.listAllChannels(key)

 for l in substruc:
  list.append(l.get("label"))

 for index, c in enumerate(channels):
  time.sleep(1)
  if c in list:
   print(index, c+ " exist")
  else:
   if index == 0:
    rootchannel = c

   else:
    print("Creating patch-channel: " + c)
    client.channel.software.create(key, c, c, "patch channel", "channel-x86_64", "", "sha1")

 try:
  time.sleep(1)
  print("Creating root patch-channel: " + rootchannel)
  client.channel.software.create(key, rootchannel, rootchannel, "patch channel", "channel-x86_64", "", "sha1")
  sublist = getSubChannels(packages)
  subPkgErrata(sublist, rootchannel)

 except:
  print(rootchannel+ " exist")

########################################################################################################################
def syncChannels(channels, packages):

 nexttopatch = getNextChannelToSync(channels)
 lastpatched = getLastSyncedChannel(channels)

 if(nexttopatch == channels[0]):
  list = getSubChannels(packages)
  subPkgErrata(list, nexttopatch)

 else:
  mergePkgErrata(lastpatched, nexttopatch)

########################################################################################################################
def getNextChannelToSync(channels):
 list = []

 nexttopatch = ""
 time = xmlrpclib.DateTime(0)

 for channel in channels:
  substruc = client.channel.software.getDetails(key, channel)
  list.append(substruc)

 for l in list:
  temp = l.get("last_modified")
  if temp < time:
   time = temp
   nexttopatch = l.get("label")

 return nexttopatch

########################################################################################################################
def getLastSyncedChannel(channels):
 list = []

 lastpatched = ""
 time = xmlrpclib.DateTime(1)

 for channel in channels:
  substruc = client.channel.software.getDetails(key, channel)
  list.append(substruc)

 for l in list:
  temp = l.get("last_modified")

  if temp > time:
   time = temp
   lastpatched = l.get("label")

 return lastpatched

########################################################################################################################
# Add packages from a list of channels to one channel
def subPkgErrata(channels, channelName):
 progress = 1
 f_max = f_str(channels)
 fin = len(channels)

 for i in channels:
  f_len = f_max - len(i) + 20
  print(("{0:<10s}{1:>"+str(f_len)+"}").format("Processing packages of channel "+str(i)+".", "["+str(progress)+"/"+str(fin)+"]"))
  client.channel.software.mergePackages(key, i, channelName)
  progress += 1

 progress = 1
 for i in channels:
  f_len = f_max - len(i) + 20
  print(("{0:<10s}{1:>"+str(f_len+2)+"}").format("Processing errata of channel "+str(i)+".", "["+str(progress)+"/"+str(fin)+"]"))
  client.channel.software.mergeErrata(key, i, channelName)
  progress += 1

########################################################################################################################
def mergePkgErrata(channelOne, channelTwo):

 print("Merging packages: "+channelOne+" --> "+channelTwo)
 client.channel.software.mergePackages(key, channelOne, channelTwo)

 print("Merging errata: "+channelOne+" --> "+channelTwo)
 client.channel.software.mergeErrata(key, channelOne, channelTwo)

 print("Merging successful.")

########################################################################################################################
def getSubChannels(packages):

 subchannellist = []

 for channel in packages:
  substruc = client.channel.software.getDetails(key, channel)
  label = substruc.get("label")
  subchannellist.append(label)

 return subchannellist

########################################################################################################################
# Creates the patch channel for the current month if it doesn't already exist.
def createRootChannel(name):
 exist = 0

 if name is None:
  channelName = "patch-channel-"+datetime.date.today().strftime("%Y-%m-%d").lower()
 else:
  channelName = name

 try:
  client.channel.software.create(key, channelName, channelName, "patch channel", "channel-x86_64", "", "sha1")

  list = getSubChannels(subchannels)
  subPkgErrata(list, channelName)

  print("Channel creation successful.")
  return True

 except:
  exist = 1
  print ("Channel already exists.")
  return False

########################################################################################################################
def main(channelOne, channelTwo):

 #client.channel.software.delete(key, "spd-patch-channel")
 #client.channel.software.delete(key, "spt-patch-channel")
 #client.channel.software.delete(key, "spp-patch-channel")

 #createPatchChannels(patchchannels, testchannels)
 #print(getNextChannelToSync(patchchannels)+ "|" +getLastSyncedChannel(patchchannels))

 #for i in range(2):
  #syncChannels(patchchannels, testchannels)
  #time.sleep(1)

 print("Hey")
 mergePkgErrata(channelOne, channelTwo)

 client.auth.logout(key)

if __name__ == "__main__":
  main()


