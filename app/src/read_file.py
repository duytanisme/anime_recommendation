from pyspark.sql.functions import col, explode
from pyspark import SparkContext
from pyspark.sql import SparkSession
import pyspark
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark import SparkConf, SparkContext
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS, ALSModel
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator, CrossValidatorModel
# from operator import add
# import sys, os, shutil
import config
#import tempfile
import json
import time

if __name__ == "__main__":
    APP_NAME="Recommendation System"
    with open('log.txt', 'w') as writer:
        writer.write(f'start\n')
    app_config = config.Config(elasticsearch_host="elasticsearch",
                               elasticsearch_port="9200",
                               elasticsearch_input_json="yes",
                               elasticsearch_nodes_wan_only="true",
                               hdfs_namenode="hdfs://namenode:9000"
                               )
    # print("init spark session")
    spark = app_config.initialize_spark_session(APP_NAME)
    
    for file_name in ['short_anime_ratings', 'rating_complete', 'long_anime_ratings']:
        txt_content = dict()
        startime = time.time()
        ratings = spark.read.csv(f"hdfs://namenode:9000/data/{file_name}.csv",header=True)
        txt_content['read_time'] = time.time() - startime
        ratings.show()
        txt_content['show_time'] = time.time() - txt_content['read_time'] - startime
        txt_content['len'] = ratings.count()
        txt_content['count_time'] = time.time() - txt_content['show_time'] - startime

        # sc = spark.sparkContext
        # spark.read.json(sc.parallelize([txt_content])).coalesce(1).write.mode('append').json('/result/model_{rank}_{regparam}.json')
        txt_content['time'] = time.time() - startime
        with open(f"/read_file/{file_name}.json", "w") as outfile:
            json.dump(txt_content, outfile)
