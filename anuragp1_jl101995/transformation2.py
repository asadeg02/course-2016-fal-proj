import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
import pandas as pd

class transformation2(dml.Algorithm):
    contributor = 'anuragp1_jl101995'
    reads = ['anuragp1_jl101995.citibike', 'anuragp1_jl101995.pedestriancounts']
    writes = ['anuragp1_jl101995.citibikecoordinates', 'anuragp1_jl101995.citibike_by_region']

    @staticmethod
    def execute(Trial = False):
    '''Retrieve some datasets'''

        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('anuragp1_jl101995', 'anuragp1_jl101995')

        citibikedata = repo.anuragp1_jl101995.citibike.find()

        repo.dropPermanent("citibikecoordinates")
        repo.createPermanent("citibikecoordinates")

        for tripdoc in citibikedata:
            tripdict = tripdoc
            coordinates = [tripdict['start station longitude'], tripdict['start station latitude']]
            # Get desired fields and add formatted location information for the CitiBike station
            tripdict = {'datetime': tripdict['starttime'],'start_station_name': tripdict['start station name'], 'gender': tripdict['gender'], \
                        'birthyear': tripdict['birth year'], 'the_geom' : {'type': 'Point', 'coordinates': coordinates}}

            # Insert document into collection
            repo.anuragp1_jl101995.citibikecoordinates.insert_one(tripdict)

        repo.anuragp1_jl101995.citibikecoordinates.ensure_index( [( 'the_geom' ,dml.pymongo.GEOSPHERE )] )
        repo.anuragp1_jl101995.pedestriancounts.ensure_index( [('the_geom' ,dml.pymongo.GEOSPHERE )] )
        repo.dropPermanent("citibike_by_region")
        repo.createPermanent("citibike_by_region")

        for this_loc in repo.anuragp1_jl101995.citibikecoordinates.find():
            closest_region = repo.command(
                'geoNear','anuragp1_jl101995.pedestriancounts',

                near={
                    'type' : this_loc['the_geom']['type'],
                    'coordinates' : this_loc['the_geom']['coordinates']},
                spherical=True,
                maxDistance = 8000

                )['results']
            citibike_by_region = {'gender' :this_loc['gender'], 'datetime' : this_loc['datetime'],'birthyear':this_loc['birthyear'], 'start_station_name': this_loc['start_station_name'],'Closest_Region' :closest_region[0]['obj']['loc']}
            repo['anuragp1_jl101995.citibike_by_region'].insert_one(citibike_by_region)

        # end database connection
        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}

    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
    '''
    Create the provenance document describing everything happening
    in this script. Each run of the script will generate a new
    document describing that invocation event.
    '''

         # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('anuragp1_jl101995', 'anuragp1_jl101995')

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('cny', 'https://data.cityofnewyork.us/resource/') # NYC Open Data 
        doc.add_namespace('mta', 'http://web.mta.info/developers/data/nyct/') # NYC MTA Data 

        # Transform associating itiBike stations with their pedestrian count regions
        this_script = doc.agent('alg:anuragp1_jl101995#transform2', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        citibike_regions_resource = doc.entity('dat:citibike_regions',{'prov:label':'CitiBike Station Region Data', prov.model.PROV_TYPE:'ont:DataSet'})
        get_citibikeregions = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_citibikeregions, this_script)
        doc.usage(get_citibikeregions, citibike_regions_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:DataSet'} )
        citibike_regions = doc.entity('dat:anuragp1_jl101995#citibike_regions', {prov.model.PROV_LABEL:'', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(citibike_regions, this_script)
        doc.wasGeneratedBy(citibike_regions, get_citibikeregions, endTime)
        doc.wasDerivedFrom(citibike_regions, citibike_regions_resource, get_citibikeregions, get_citibikeregions, get_citibikeregions) 

        # CitiBike Data
        citibike_resource = doc.entity('cbd:tripdata', {'prov:label':'CitiBike Trip Data', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'csv'})
        get_citibike = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_citbike, this_citibike)
        doc.usage(get_citibike, citibike_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval'} )
        citibike = doc.entity('dat:anuragp1_jl101995#citibike', {prov.model.PROV_LABEL:'', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(citibike, this_script)
        doc.wasGeneratedBy(citibike, get_citibike, endTime)
        doc.wasDerivedFrom(citibike, citibike_resource, get_citibike, get_citbike, get_citibike)

        # Pedestrians Count Data 
        pedestrian_resource = doc.entity('dat:pedestriancounts',{'prov:label':'Pedestrians Count Data', prov.model.PROV_TYPE:'ont:DataSet'})
        get_pedestrian = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_pedestrian, this_script)
        doc.usage(get_pedstrian, pedstrian_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:DataSet'} )
        pedestrian = doc.entity('dat:anuragp1_jl101995#pedestriancounts', {prov.model.PROV_LABEL:'NYC Bi-Annual Pedestrian Counts', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(pedestrian, this_script)
        doc.wasGeneratedBy(pedestrian, get_pedestrian, endTime)
        doc.wasDerivedFrom(pedestrian, pedestrian_resource, get_pedestrian, get_pedestrian, get_pedestrian) 
        
        repo.record(doc.serialize()) # Record the provenance document.
        repo.logout()
        
        return doc


transformation2.execute()
doc = transformation2.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

# eof
