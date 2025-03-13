# coding=utf-8
import pyspark
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession

from operator import add
import sys,os
from pyspark.sql.types import *

import config, io_cluster

# schema = StructType([
#       StructField("user_id",StringType(),True),
#       StructField("username",StringType(),True)
#   ])

if __name__ == "__main__":
    APP_NAME = "PreprocessData"
    print("start")
    print("------------------------------------------------------------------------------------------------------")

    app_config = config.Config(elasticsearch_host="elasticsearch",
                               elasticsearch_port="9200",
                               elasticsearch_input_json="yes",
                               elasticsearch_nodes_wan_only="true",
                               hdfs_namenode="hdfs://namenode:9000"
                               )
    print("init spark session")
    print("------------------------------------------------------------------------------------------------------")
    spark = app_config.initialize_spark_session(APP_NAME)
    print("read file csv")
    print("------------------------------------------------------------------------------------------------------")

    df_anime_list = spark.read.csv("hdfs://namenode:9000/data/animelist.csv")
    df_anime_list.createOrReplaceTempView("animelist")

    df_anime = spark.read.csv("hdfs://namenode:9000/data/anime.csv")
    df_anime.createOrReplaceTempView("anime")

    df_rating = spark.read.csv("hdfs://namenode:9000/data/rating_complete.csv")
    df_rating.createOrReplaceTempView("rating")

    df_genres = spark.read.csv("hdfs://namenode:9000/data/genres.csv")
    df_genres.createOrReplaceTempView("genres")

    #1 add animelist
    anime_list = spark.sql("Select a._c0 as userId, a._c1 as animeId, a._c2 as rating, a._c3 as watchingStatus, a._c4 as watchedEpisodes from animelist a ")

    #2 add anime
    anime = spark.sql("Select a._c0 as animeId, a._c1 as name, a._c2 as scores, a._c3 as genres, a._c6 as type, a._c7 as episodes, a._c12 as studio, a._c13 as source, a._c15 as rating, a._c16 as ranking from anime a")

    #3 add rating
    rating = spark.sql("Select r._c0 as userId, r._c1 as animeId, r._c2 as rating from rating r")

    #4 add animelist join anime
    animeTotalWatches =  spark.sql("Select alist._c1 as animeId, sum(alist._c4) as totalWatchedEpisodes, a._c1 as name, a._c2 as scores, a._c3 as genres, a._c6 as type, a._c7 as episodes, a._c12 as studio, a._c13 as source, a._c15 as rating, a._c16 as ranking from anime a, animelist alist where a._c0 = alist._c1 group by alist._c1, a._c1, a._c2, a._c3, a._c6, a._c7, a._c12, a._c13, a._c15, a._c16")
    animeTotalWatches.createOrReplaceTempView("total_views_anime")

    #5 add userTotalWatched
    userTotalWatched = spark.sql("Select a._c0 as userId, sum(a._c4) as userWatchedEpisodes from animelist a group by a._c0")

    #6 animelist 100 users
    top_100_users = spark.sql("Select al._c0 as userId, al._c1 as animeId, al._c2 as rating, al._c3 as watchingStatus, al._c4 as watchedEpisodes, a._c0 as animeId, a._c1 as name, a._c2 as scores, a._c3 as genres, a._c6 as type, a._c7 as episodes, a._c12 as studio, a._c13 as source, a._c15 as rating, a._c16 as ranking from animelist al, anime a where al._c0 < 101 and al._c1 = a._c0")


    # genres_header.append("TotalEps")
    # print("genres header: ", genres_header)

    io_cluster.save_dataframes_to_elasticsearch(
        (anime, rating, animeTotalWatches, userTotalWatched),
        ("anime", "rating", "anime_total_watches", "user_total_watched"),
        app_config.get_elasticsearch_conf()
    )

    # io_cluster.save_dataframes_to_elasticsearch2(top_100_users, "top_100_users", app_config.get_elasticsearch_conf())
