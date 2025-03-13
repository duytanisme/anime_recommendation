# PTPM_GROUP_1

<div align="center">

# Hệ thống phân tích và dự đoán phim Anime

</div>

## Contributors
+ Trần Mỹ Linh
+ Mai Trọng Nghĩa
+ Nguyễn Thị Quý
+ Bùi Duy Tân
+ Nguyễn Hương Trà

## Data preparation
[MyAnimeList](https://myanimelist.net/) and [Kaggle](https://www.kaggle.com/datasets/hernan4444/anime-recommendation-database-2020?select=rating_complete.csv&fbclid=IwAR37KBNhDMUmDlL2he0iLylicmXE4KjugeiNUarZjhUH-oqHNOtHkYVjvQ4)
## Procedure

Start the system
```bash
cd app
docker-compose up -d
```

Copy source files from host to containers:
```bash
docker cp src spark-master:/
docker cp libs/elasticsearch-hadoop-7.15.1.jar spark-master:elasticsearch-hadoop-7.15.1.jar
```

Copy processed data to namenode:
```bash
docker cp ../data/movies/anime.csv namenode:/
docker cp ../data/movies/animelist.csv namenode:/
docker cp ../data/movies/anime_refined_modified.csv namenode:/
docker cp ../data/ratings/rating_complete.csv namenode:/
docker cp ../data/ratings/short_anime_ratings.csv namenode:/
docker cp ../data/ratings/long_anime_ratings.csv namenode:/
```

Push data to HDFS:
```bash
docker exec -it namenode /bin/bash
hdfs dfs -mkdir /data/
hdfs dfs -mkdir /model/
hdfs dfs -mkdir /result/
hdfs dfs -put short_anime_ratings.csv /data/
hdfs dfs -put rating_complete.csv /data/
hdfs dfs -put long_anime_ratings.csv /data/
hdfs dfs -put anime.csv /data/
hdfs dfs -put animelist.csv /data/
hdfs dfs -put anime_refined_modified.csv /data/
exit
```

Create directory for models in Spark master node:
```bash
docker exec -it spark-master /bin/bash
mkdir -p /result/model/
mkdir -p /result/spark_nodes/
mkdir -p /result/read_file/
```

Install required packages:
```bash
python3 -m venv .venv
source .venv/bin/activate
apk update
apk add make automake gcc g++ subversion python3-dev
pip3 install numpy venv-pack flask
```

> [!WARNING]
> For some reasons, python versions in Spark master and Spark worker are different (I guess due to the installation right above). To fix this error, follow this:

Exit the Spark master node:
```bash
exit
```

Enter the Spark worker node:
```bash
docker exec -it spark-worker-a /bin/bash
apk update
apk add nano
nano spark/conf/spark-env.sh.template
```

Then go to the bottom of the file, and add these 2 lines:
```
export PYSPARK_PYTHON=/usr/local/bin/python3.7
export PYSPARK_DRIVER_PYTHON=/usr/local/bin/python3.7
```

Then `Ctrl+X`, `Y` and `Enter` to save the file.

After that, exit the Spark worker node:
```bash
exit
```

Run python, with `elasticsearch` is optional:
```bash
docker exec -it /bin/bash
source .venv/bin/bash
spark/bin/spark-submit --master spark://spark-master:7077 --jars elasticsearch-hadoop-7.15.1.jar --driver-class-path elasticsearch-hadoop-7.15.1.jar src/als_anime.py
```

> [!NOTE]
> The model output is temporarily stored on HDFS. To access the API (currently under development), run the following command:
```bash
spark/bin/spark-submit src/dev.py
```

The API can be accessed from both the spark-master node and the host computer through port `5000`. To make a request, use the following curl command:
```bash
curl "http://localhost:5000/recommend?user_id=1&year=2020&limit=1&include_metadata=true"
```
