import datetime
import psycopg2
import sys

class AggregatorQuerier():
    """
    Class for making queries to the database, not thread safe
    """

    ###########################################################################
    # Class constants 
    ###########################################################################

    # Default value of how many minutes back to query in default case
    _DEFAULT_QUERY_WINDOW=10

    ###########################################################################
    # Constructors
    ###########################################################################

    def __init__(self, dbname, dbuser, query_window=_DEFAULT_QUERY_WINDOW):
        try:
            self._con = psycopg2.connect(database=dbname, user=dbuser)
        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e

    ###########################################################################
    # Public utility functions 
    ###########################################################################

    def close(self):
        try:
            self._con.close()
        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e
        except:
            print "Couldn't close DB connection"

    ###########################################################################
    # Public aggregator queries
    ###########################################################################

    def get_last_memory_util(self, aggregate):
        """
        Get the latest value of memory utilization for a given aggregate
        """
        #internal_result = self._get_metric_by_aggregate_latest_first, aggregate, "memory_util")

        # FIXME: fake data for now
        internal_result = { "pc1" : [ { "time" : 5, "value" : .2 }, 
                                      { "time" : 4, "value" : .25 } ],
                            "pc2" : [ { "time" : 5, "value" : .1 }, 
                                      { "time" : 4, "value" : .15 } ], 
                            "pc3" : [ { "time" : 5, "value" : .3 }, 
                                      { "time" : 4, "value" : .35 } ] }

        external_result = {}

        for resource in internal_result:
            # This assumes that the query sorted descending by time
            external_result[resource] = internal_result[resource][0]["value"]
            
        return external_result


    ###########################################################################
    # Private utility methods
    ###########################################################################

    def _datetime_to_db_timestamp(dt):
        """
        Converts a python datetime object to a timestamp in the format
        that the querier requires
        """
        epoch = datetime.datetime.utcfromtimestamp(0)
        delta = dt - epoch
        return delta.total_seconds() * 1000.0

    def _get_metric_by_aggregate(self, aggregate, metric, since=None):
        """
        Queries for a specific metric associated with an aggregate
        from a time frame up to this point in time, orders results
        from most recent data to least recent within window
        """

        # If since is unset, make it default 
        if since is None:
            since = datetime.datetime.now() - \
                    datetime.timedelta(minutes=self.query_window)

        # Convert datetime timestamp to db format
        since = _datetime_to_db_timestamp(since_dt)

        # Form the query
        query = ("SELECT resource_id,time,value FROM %s "
                 "WHERE time > %s ORDER BY time DESC;")
        args = (metric, since,)

        try:
            # Get a cursor and make the query
            cur = self._con.cursor()
            cur.execute(query, args)

            result = {}

            # Build the return value from the records
            for record in cur:
                resource_id = record[0]
                time = record[1]
                value = record[2]

                if not resource_id in result:
                    result[resource_id] = []
                    measurement = { "time" : time, "value" : value }
                
                result[resource_id].append(measurement)

            # Close the cursor now that our object is built
            cur.close()

        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e

        return result

    ###########################################################################
    # Unit testing code 
    ###########################################################################

    def run_unit_test(self, aggregate):
        result = self.get_last_memory_util(aggregate)
        
        print result

        for resource in result:
            print "gpo-ig[%s] latest memory utilization is: %s" % \
                (resource, result[resource])

        return 0

if __name__ == "__main__":
    querier = AggregatorQuerier("aggregator", "rirwin")
    val = querier.run_unit_test("gpo-ig")
    querier.close()
    sys.exit(val)
