from pyspark.sql.functions import col, explode
from pyspark import SparkContext
from pyspark.sql import SparkSession
import pyspark
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark import SparkConf, SparkContext
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator, CrossValidatorModel
from operator import add
import sys,os
import config
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.linalg import Vectors
import tempfile

if __name__ == "__main__":
    APP_NAME="LoadData"
    print("start")
    app_config = config.Config(elasticsearch_host="elasticsearch",
                            elasticsearch_port="9200",
                            elasticsearch_input_json="yes",
                            elasticsearch_nodes_wan_only="true",
                            hdfs_namenode="hdfs://namenode:9000"
                            )
    # print("init spark session")
    spark = app_config.initialize_spark_session(APP_NAME)
    # print("read file csv")

    sc = SparkContext
    cvModelRead = CrossValidatorModel.load('/model')
    print(cvModelRead.avgMetrics)
    best_model = model.bestModel
    print(type(best_model))

    # Complete the code below to extract the ALS model parameters
    print("**Best Model**")

    # # Print "Rank"
    print("  Rank:", best_model._java_obj.parent().getRank())

    # Print "MaxIter"
    print("  MaxIter:", best_model._java_obj.parent().getMaxIter())

    # Print "RegParam"
    print("  RegParam:", best_model._java_obj.parent().getRegParam())
