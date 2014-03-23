#!/usr/bin/env python

from bs4 import BeautifulSoup, Comment
import mechanize, psycopg2
from datetime import datetime, timedelta
from dateutil import parser
from dateutil.tz import *
from geojson import Point, Feature, FeatureCollection
from osgeo import ogr, osr
from decimal import Decimal

def get_source(targetURL, *args):
    br = mechanize.Browser()
        
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    
    br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.53 Safari/525.19')]
    
    response = br.open(targetURL)
    if args:
        soup = BeautifulSoup(response.read(), args[0])
    else:
        soup = BeautifulSoup(response.read())
    
    return(soup)

def get_CDF_fires():
    soup = get_source("http://cdfdata.fire.ca.gov/incidents/rss.xml", "xml")
    cdfIncidents = soup('item')
    CDFCoordinates = get_CDF_incident_coordinates()
    rssDetails = {}
    for fire in cdfIncidents:
        rssName = fire.title.string.split(" (")[0] #cuts off everything after XXXXX Fire (sometimes just XXXX)
        if rssName.rfind(' Fire') is not -1:
            rssName = rssName[0:rssName.rfind(' Fire')] #cuts off 'Fire' from end of name
        if rssName in CDFCoordinates.keys(): #matches incidents from RSS feed with incidents from gmap/kml
            rssLink = fire.link.string
            pubDate = fire.pubDate.string
            lastUpdate = parser.parse(pubDate)
            
            #actually attaches coordinates from gmap/kml to incident record
            
            rssLon = CDFCoordinates[rssName][0] 
            try:
                rssLon = float(rssLon)
            except Exception:
                rssLon = None
            rssLat = CDFCoordinates[rssName][1] 
            try:
                rssLat = float(rssLat)
            except Exception:
                rssLat = None
                
                
            #if it all worked, complete mapping of incident to dict, then add to dict of all CDF incidents
            
            if type(rssLat) == float and type(rssLon) == float: 
                rssDetails[rssName] = {'name':rssName, 'last_update':lastUpdate, 'link':rssLink, 'longitude':rssLon, 'latitude':rssLat}
    return rssDetails
    
        
        

def get_CDF_incident_coordinates():
    br = mechanize.Browser()
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.53 Safari/525.19')]
    
    #on CDF hosted gmap, find the the link to the google hosted CDF map, then parse to find the string showing the particular KML file used as data for the google hosted page.  That's only way to make sure we've got the latest updated KML file.
    
    response = br.open('http://www.calfire.ca.gov/general/firemaps.php')
    gmapURL = br.find_link(text="California Fire Map").url
    kmlKey = gmapURL[(gmapURL.find('msid=') +5):(gmapURL.find('msid=') + 48)]
    mappedIncidents = parse_CDF_KML(kmlKey)
    return mappedIncidents
    #return get_CDF_locations(kmlKey)


def parse_CDF_KML(kmlKey):
    soup = get_source('https://maps.google.com/maps/ms?ie=UTF8&hl=en&source=embed&msa=0&output=kml&msid=' + kmlKey, 'xml')
    KML_Incidents = soup('Placemark')
    #activeCDF = soup('Placemark')
    mappedIncidents = {}
    for incident in KML_Incidents:
        incidentName = incident('name')[0].string
        if incidentName.rfind(' Fire') is not -1:
            incidentName = incidentName[0:incidentName.rfind(' Fire')]
        incidentCoords = incident('coordinates')[0].string
        incidentLon = incidentCoords.split(',')[0]
        incidentLat = incidentCoords.split(',')[1]
        mappedIncidents[incidentName] = (incidentLon, incidentLat)
    return mappedIncidents
    

def scrapeCDFDetails(fire):
    soup = get_source(fire.get('link'))
    try:
        fire['location'] = soup.find('td', text='Location:').find_next_sibling('td').string.rstrip()
    except Exception:
        pass
    
    if soup.find('td', text="Estimated - Containment: ") != None:
        try:
            fire['acres'] = soup.find('td', text='Estimated - Containment: ').find_next_sibling('td').contents[0].split()[0]
        except Exception:
            pass
        try:
            fire['containment'] = soup.find('font').string
        except Exception:
            pass
    else:
        try:
            acresContain = soup.find('td', text='Acres Burned - Containment: ').find_next_sibling('td').contents[0].split()
            fire['acres'] = acresContain[0]
            fire['containment'] = acresContain[-2]
        except Exception:
            pass
    return fire


        
def get_nat_fires():
    natIncidents = get_source('http://inciweb.nwcg.gov/feeds/rss/incidents/state/5/' )
    comments = natIncidents.findAll(text=lambda text:isinstance(text, Comment))
    cache = comments[0].splitlines()[-1].split()[-1]
    natDetails = {}
    fires = natIncidents('item')
    for fire in fires:
        natName = fire.title.string.split(" (")[0] #splits off (wildfire) or (prescribed fire) from name
        if natName.rfind(' Fire') is not -1: #splits off "Fire" from name if present, to match with CDF incidents
            natName = natName[0:natName.rfind(' Fire')]
        natType = fire.title.string.split(" (")[-1][:-1] #grabs (wildfire) or (prescribed fire) 
        natPubDate = parser.parse(fire.pubdate.string)
        natLatitude = fire.find('geo:lat').string
        try:
            natLatitude = float(natLatitude)
        except:
            natLatitude = None
        natLongitude = fire.find('geo:long').string
        try:
            natLongitude = float(natLongitude)
        except Exception:
            natLongitude = None
        natLink = fire.guid.string
        if natType == "Wildfire" and type(natLongitude) == float and type(natLongitude) == float:
            natDetails[natName] = {'name':natName, 'last_update':natPubDate, 'latitude':natLatitude, 'longitude':natLongitude, 'link':natLink} #, 'details':natDescription}
    return natDetails


def scrapeNationalDetails(fire):
    soup = get_source(fire.get('link'))
    try:
        fire['location'] = soup.find('th', text="Location").find_next_sibling().string
    except Exception:
        pass
    try:
        fire['acres'] = soup.find('th', text="Size").find_next_sibling().string.split()[0]
    except Exception:
        pass
    try:
        fire['containment'] = soup.find('th', text="Percent Contained").find_next_sibling().string
    except Exception:
        pass
    return fire
    




national = get_nat_fires()
cdf = get_CDF_fires()


fireList = [] #this will be single, clean, ~canonical record of wildfire incidents regardless of jurisdiction. 
    
for k in cdf.keys():
    if k not in national.keys():
        fire = cdf.get(k)
        fire = scrapeCDFDetails(fire)
        fireList.append(fire)
    elif k in national.keys():
        if cdf.get(k).get('last_update') > national.get(k).get('last_update'):
            fire = cdf.get(k)
            fire = scrapeCDFDetails(fire)
            fire['longitude'] = national.get(k).get('longitude') #replaces CDF coordinates with USFS coords because feds usually have better mapping
            fire['latitude'] = national.get(k).get('latitude')
            fireList.append(fire)
            try:
                del national[k] #don't want dupes in final list
            except KeyError:
                pass



for k in national.keys():
    fire = national.get(k)
    fire = scrapeNationalDetails(fire)
    fireList.append(fire)
    






#Commented out code would reproject incidents to 3857.  OpenLayers can handle in client side, so leaving as 4326
  
#sourceSR = osr.SpatialReference()
#sourceSR.ImportFromEPSG(4326)

#targetSR = osr.SpatialReference()
#targetSR.ImportFromEPSG(3857)

#coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)

#wkt = "POINT (%f %f)" % (float(fire.get('longitude')), float(fire.get('latitude')))
#firePoint = ogr.CreateGeometryFromWkt(wkt)
#firePoint.Transform(coordTrans)    
#firePoint = Point((firePoint.GetY(), firePoint.GetX()))


featureList = []


for fire in fireList:
    
    
    firePoint = Point((fire.get('longitude'), fire.get('latitude')))
    if fire['last_update'] <= (datetime.now(tzlocal()) - timedelta(weeks=2, hours=6)):
        fire['status'] = 'inactive'
    elif 'containment' in fire and fire['containment'] == "100%":
            fire['status'] = 'inactive'
    else:
        fire['status'] = 'active'
    fire['last_update'] = fire['last_update'].strftime("%b %d %Y %H:%M:%S")
    fireObject = Feature(geometry=firePoint, properties=fire, id=fire['name'])
    featureList.append(fireObject)


wildfires = FeatureCollection(featureList)

outDir = "/opt/projects/wildfire/california-firetracker/"

outfile = open(outDir + "wildfires.geojson", "w")
outfile.write(str(wildfires))
outfile.close()


