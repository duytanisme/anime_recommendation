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
app = Flask(__name__)


def init_spark():
    global spark, best_model

    APP_NAME = "Recommendation System"
    spark = SparkSession.builder.appName(APP_NAME).getOrCreate()

    model_path = "hdfs://namenode:9000/model/model_200_0.1"
    cross_validator_model = CrossValidatorModel.load(model_path)
    best_model = cross_validator_model.bestModel
    print("Spark initialized and model loaded successfully")


@app.route("/recommend", methods=["GET"])
def get_recommendations():
    global spark, best_model
    start_time = time.time()

    user_id = request.args.get("user_id", type=int)
    num_recs = request.args.get("num_recommendations", default=10, type=int)

    if not user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400

    try:
        user_df = spark.createDataFrame([(user_id,)], ["user_id"])
        recommendations = best_model.recommendForUserSubset(user_df, num_recs)
        result = (
            recommendations.select(
                "user_id", explode("recommendations").alias("rec")
            )
            .select(
                "user_id",
                col("rec.anime_id").alias("anime_id"),
                col("rec.rating").alias("predicted_rating"),
            )
            .collect()
        )

        recommendations_list = [
            {
                "anime_id": row["anime_id"],
                "predicted_rating": float(row["predicted_rating"]),
            }
            for row in result
        ]

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
