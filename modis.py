#!/usr/bin/env python

from datetime import datetime, timedelta
from dateutil import parser
from geojson import Point, Feature, FeatureCollection
from urllib2 import Request, urlopen, URLError, HTTPError
from osgeo import ogr, osr



def scrape_modis():
    req = Request("https://firms.modaps.eosdis.nasa.gov/active_fire/text/USA_contiguous_and_Hawaii_7d.csv")
    attempt = 0
    while attempt < 4:
        try:
            return urlopen(req).readlines()[1:]
        except HTTPError, e:
            print "HTTP Error:",e.code , url 
        except URLError, e:
            print "URL Error:",e.reason , url
        time.sleep(300)
        attempt += 1
        
modis = scrape_modis()

#for testing
#modisFile = open('/home/aidian/fire/fire-env/USA_contiguous_and_Hawaii_7d.csv', 'r')
#modis = modisFile.readlines()[1:]

sourceSR = osr.SpatialReference()
sourceSR.ImportFromEPSG(4326)

targetSR = osr.SpatialReference()
targetSR.ImportFromEPSG(3857)

coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)

#####very rough bbox for Cali#####

y1 = 31.0000
y2 = 43.0000

x1 = -113.0000
x2 = -126.0000


outDir = '/opt/projects/wildfire/california-firetracker/'

outfile24 = open(outDir + 'modis24.geojson', "w")
outfile48 = open(outDir + 'modis48.geojson', "w")
outfile7 = open(outDir + 'modis7.geojson', "w")

modis24 = []
modis48 = []
modis7 = []

for z in range(len(modis)):
    detection = modis[z].split(',')
    py = float(detection[0])
    px = float(detection[1])
    confidence = int(detection[8])
    if px < x1 and px > x2 and py > y1 and py < y2 and confidence >= 50: #confidence 50 is arbitrary value
        #datetime_detected needed for parsing category (24,48,7), separate detected is for display to user
        datetime_detected = parser.parse(str(detection[5]) + str(detection[6]))
        detected = datetime_detected - timedelta(hours=8)
        detected = detected.strftime("%b %d %Y %H:%M:%S")
        modisIncident = {'longitude':px, 'latitude':py, 'detected':detected}
        
        
        wkt = "POINT (%f %f)" % (px, py)
        ogrPoint = ogr.CreateGeometryFromWkt(wkt)
        ogrPoint.Transform(coordTrans)
        wkt = ogrPoint.ExportToWkt()
        
        
        
        
        modisPoint = Point((ogrPoint.GetX(), ogrPoint.GetY())) #GeoJSON point
        modisObject = Feature(geometry=modisPoint, properties=modisIncident)
        if datetime_detected > datetime.utcnow() - timedelta(hours=24):
            modisObject.properties['group'] = 24
            modis24.append(modisObject)
        elif datetime_detected > datetime.utcnow() - timedelta(hours=48):
            modisObject.properties['group'] = 48
            modis48.append(modisObject)
        else:
            modisObject.properties['group'] = 7
            modis7.append(modisObject)
            
        #modisList.append(modisObject)
    
proj = '"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/sr-org/7483/ogcwkt/", "type": "ogcwkt"}}'

modis24.append(proj)
modis48.append(proj)
modis7.append(proj)
    
    
modis24Out = FeatureCollection(modis24)
modis48Out = FeatureCollection(modis48)
modis7Out = FeatureCollection(modis7)

outfile24.write(str(modis24Out))
outfile48.write(str(modis48Out))
outfile7.write(str(modis7Out))

outfile24.close()
outfile48.close()
outfile7.close()

        

        
        
        
    
        
    
        
        
