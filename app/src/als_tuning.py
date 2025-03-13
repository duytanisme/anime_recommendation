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
import io_cluster
#importing the module 
import logging 
import time

if __name__ == "__main__":
    startime = time.time()
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
    # print("read file csv")

    # import subprocess
    # proc = subprocess.Popen(["hdfs", "dfs", "-copyFromLocal", "-f", "/result/model.json", "hdfs://namenode:9000/result/model.json"])
    # proc.communicate()


    # df = spark.read.json("/result/model.json",multiLine=True)
    # df.write.mode("overwrite").json("hdfs://namenode:9000/result/model.json")

    sc = SparkContext
    # sc.setCheckpointDir('checkpoint')
    # spark = SparkSession.builder.appName('Recommendations').getOrCreate()

    ratings = spark.read.csv("hdfs://namenode:9000/data/rating_complete.csv",header=True)

    # ratings.show()
    # ratings.printSchema()

    ratings = ratings.\
        withColumn('user_id', col('user_id').cast('integer')).\
        withColumn('anime_id', col('anime_id').cast('integer')).\
        withColumn('rating', col('rating').cast('float'))
    # ratings.show()


    # Group data by userId, count ratings
    userId_ratings = ratings.groupBy("user_id").count().orderBy('count', ascending=False)
    # userId_ratings.show()

    # Group data by userId, count ratings
    movieId_ratings = ratings.groupBy("anime_id").count().orderBy('count', ascending=False)

    # Create test and train set
    (train, test) = ratings.randomSplit([0.8, 0.2], seed = 1234)

    # Create ALS model
    als = ALS(userCol="user_id", itemCol="anime_id", ratingCol="rating", nonnegative = True, implicitPrefs = False, coldStartStrategy="drop")

    # Confirm that a model called "als" was created
    with open('log.txt', 'a') as writer:
        writer.write(f'{type(als)}\n')
    #print(type(als))

    # Add hyperparameters and their respective values to param_grid
    # param_grid = ParamGridBuilder() \
    #             .addGrid(als.rank, [10, 50, 100, 150]) \
    #             .addGrid(als.regParam, [.01, .05, .1, .15]) \
    #             .build()
                #             .addGrid(als.maxIter, [5, 50, 100, 200]) \
    for rank in [10, 50, 100]:
        for regParam in [.01, .05, .1, .15]:
            param_grid = ParamGridBuilder() \
                        .addGrid(als.rank, [rank]) \
                        .addGrid(als.regParam, [regParam]) \
                        .build()
                        #             .addGrid(als.maxIter, [5, 50, 100, 200]) \

                    
            # Define evaluator as RMSE and print length of evaluator
            evaluator = RegressionEvaluator(metricName="rmse", labelCol="rating", predictionCol="prediction") 
            print ("Num models to be tested: ", len(param_grid))



            # Build cross validation using CrossValidator
            cv = CrossValidator(estimator=als, estimatorParamMaps=param_grid, evaluator=evaluator, numFolds=5)

            # Confirm cv was built
            print(cv)

            #Fit cross validator to the 'train' dataset
            model = cv.fit(train)
            with open('log.txt', 'a') as writer:
                writer.write(f'{type(model)}\n')
            #print(type(model))
            with open('log.txt', 'a') as writer:
                writer.write(f'{type(model)}\n')
            

            # Save model
            # print(model.getNumFolds())
            # print(model.avgMetrics[0])
            # path = tempfile.mkdtemp()
            # print(path)
            # model_path = path + "/model"
            # model.write().save(model_path)
            
            # model.write().overwrite().save('/model/')
            # cvModelRead = CrossValidatorModel.read().load('/model/')

            #Extract best model from the cv model above
            best_model = model.bestModel

            # Print best_model
            with open('log.txt', 'a') as writer:
                writer.write(f'{type(best_model)}\n')

            # txt_content = dict()
            txt_content = dict()
            # Complete the code below to extract the ALS model parameters
            print("**Best Model**")

            # # Print "Rank"
            print("  Rank:", best_model._java_obj.parent().getRank())
            txt_content['rank'] = best_model._java_obj.parent().getRank()
            # txt_content.append({'rank': best_model._java_obj.parent().getRank()})

            # Print "MaxIter"
            print("  MaxIter:", best_model._java_obj.parent().getMaxIter())
            txt_content['maxiter'] = best_model._java_obj.parent().getMaxIter()
            # txt_content.append({'maxiter': best_model._java_obj.parent().getMaxIter()})

            # Print "RegParam"
            print("  RegParam:", best_model._java_obj.parent().getRegParam())
            txt_content['regparam'] = best_model._java_obj.parent().getRegParam()
            # txt_content.append({'regparam': best_model._java_obj.parent().getRegParam()})

            # View the predictions
            test_predictions = best_model.transform(test)
            RMSE = evaluator.evaluate(test_predictions)
            txt_content['rmse'] = RMSE
            #txt_content.append({'rmse': RMSE})
            test_predictions.show()

            with open('log.txt', 'a') as writer:
                writer.write(f'{str(txt_content)}\n')

            rank = txt_content['rank']
            regparam = txt_content['regparam']
            json_object = json.dumps(txt_content, indent=4)

            # sc = spark.sparkContext
            # spark.read.json(sc.parallelize([txt_content])).coalesce(1).write.mode('append').json('/result/model_{rank}_{regparam}.json')
            txt_content['time'] = time.time() - startime
            with open(f"/result/model_{rank}_{regparam}.json", "w") as outfile:
            # with open(f"/result/spark_nodes/model_5_core.json", "w") as outfile:
                json.dump(txt_content, outfile)
            # df = spark.createDataFrame(data=txt_content, schema = ["name","properties"])
            model.write().overwrite().save(f'/model/model_{rank}_{regparam}')
            model.write().overwrite().save(f'hdfs://namenode:9000/model/model_{rank}_{regparam}')
            model = CrossValidatorModel.read().load(f'hdfs://namenode:9000/model/model_{rank}_{regparam}')
            best_model = model.bestModel
            # df.write.mode("overwrite").csv("hdfs://namenode:9000/result/model.csv", format='csv', )
            # df.write.mode("overwrite").csv("hdfs://namenode:9000/result/model.csv")
            # df.write.option("header","true").csv("hdfs://namenode:9000/result/csvfile")
            
            # df_to_hdfs=(df,)
            # df_hdfs_name = ("model1.json",)
            # io_cluster.save_dataframes_to_hdfs("result/", app_config, df_to_hdfs, df_hdfs_name)

            




