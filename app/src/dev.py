from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS, ALSModel
from pyspark.ml.tuning import CrossValidatorModel
from pyspark.sql.functions import col, explode
import time
import os
from flask import Flask, request, jsonify
import threading
import atexit

spark = None
best_model = None
anime_df = None
app = Flask(__name__)


def init_spark():
    global spark, best_model, anime_df
    APP_NAME = "Recommendation System"
    spark = SparkSession.builder.appName(APP_NAME).getOrCreate()

    model_path = "hdfs://namenode:9000/model/model_200_0.1"
    cross_validator_model = CrossValidatorModel.load(model_path)
    best_model = cross_validator_model.bestModel

    anime_data_path = "hdfs://namenode:9000/data/anime_refined_modified.csv"
    anime_df = spark.read.csv(anime_data_path, header=True, inferSchema=True)

    print("Spark initialized and model loaded successfully")
    print("Anime metadata loaded successfully")


@app.route("/recommend", methods=["GET"])
def get_recommendations():
    global spark, best_model, anime_df
    start_time = time.time()

    user_id = request.args.get("user_id", type=int)
    num_recs = request.args.get("limit", default=10, type=int)
    include_metadata = (
        request.args.get("include_metadata", default="false").lower() == "true"
    )
    year_filter = request.args.get("year", type=int)

    if not user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400

    try:
        user_df = spark.createDataFrame([(user_id,)], ["user_id"])
        recommendations = best_model.recommendForUserSubset(user_df, num_recs)

        rec_df = recommendations.select(
            "user_id", explode("recommendations").alias("rec")
        ).select(
            "user_id",
            col("rec.anime_id").alias("anime_id"),
            col("rec.rating").alias("predicted_rating"),
        )

        if year_filter:
            filtered_anime = anime_df.filter(col("year") == year_filter)
            rec_df = rec_df.join(
                filtered_anime.select("anime_id"), "anime_id", "inner"
            )

        if include_metadata:
            rec_df = rec_df.join(anime_df, "anime_id", "inner")

        if year_filter and rec_df.count() < num_recs:
            additional_recs = num_recs * 3
            user_df = spark.createDataFrame([(user_id,)], ["user_id"])
            recommendations = best_model.recommendForUserSubset(
                user_df, additional_recs
            )

            additional_rec_df = recommendations.select(
                "user_id", explode("recommendations").alias("rec")
            ).select(
                "user_id",
                col("rec.anime_id").alias("anime_id"),
                col("rec.rating").alias("predicted_rating"),
            )

            if year_filter:
                additional_rec_df = additional_rec_df.join(
                    filtered_anime.select("anime_id"), "anime_id", "inner"
                )

            if include_metadata:
                additional_rec_df = additional_rec_df.join(
                    anime_df, "anime_id", "inner"
                )

            rec_df = rec_df.union(additional_rec_df).distinct()

        rec_df = rec_df.limit(num_recs)
        result = rec_df.collect()

        recommendations_list = []
        for row in result:
            rec_item = {
                "anime_id": row["anime_id"],
                "predicted_rating": round(float(row["predicted_rating"]), 2),
            }

            if include_metadata:
                for field in anime_df.schema.fieldNames():
                    if field != "anime_id" and field in row:
                        rec_item[field] = row[field]

            recommendations_list.append(rec_item)

        response = {
            "user_id": user_id,
            "recommendations": recommendations_list,
            "processing_time": f"{time.time() - start_time:.2f} seconds",
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def shutdown_spark():
    global spark
    if spark:
        spark.stop()
        print("Spark session stopped")


def run_flask():
    app.run(host="0.0.0.0", port=5000, use_reloader=False)


if __name__ == "__main__":
    init_spark()
    atexit.register(shutdown_spark)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("Press CTRL+C to exit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
