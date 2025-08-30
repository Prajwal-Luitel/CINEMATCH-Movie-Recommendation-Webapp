from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings


from movies.models import MovieMetadata, MasterTable

import os
from pyspark.sql import SparkSession
from pyspark.ml.feature import BucketedRandomProjectionLSHModel
from pyspark.sql import functions as F

from django.shortcuts import render
from django.db.models import Avg

spark_config = settings.SPARK_CONFIG

spark = (
    SparkSession.builder
    .master(f"spark://{spark_config['master_ip']}:7077")
    .appName("cinematch")
    .config("spark.driver.memory", spark_config["driver_memory"])
    .config("spark.executor.memory", spark_config["executor_memory"])
    .config("spark.executor.cores", spark_config["executor_cores"])
    .config("spark.executor.instances", spark_config["executor_instances"])
    .config("spark.sql.shuffle.partitions", "4")
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    .config("spark.kryoserializer.buffer.max", "500M")
    .getOrCreate()
)

INPUT_PATH = "s3a://movie-recommendationsystem/transform/"

# Load once
lsh_model = BucketedRandomProjectionLSHModel.load(
    os.path.join(INPUT_PATH, "stage2/lsh_model")
)
vector_df = spark.read.parquet(os.path.join(INPUT_PATH, "stage4/vector"))


def get_recommendations(movie_id, top_k=5):
    # Get query vector
    movie_vector = vector_df.filter(F.col("id") == movie_id).limit(1)
    # print(f"{movie_vector.show()}")

    # print(f"after it")

    if movie_vector.count() == 0:
        print(f"huh what happen")
        return []

    query_vec = movie_vector.first()["norm_features"]
    # print(f"query_vec't go  {query_vec}")
    # Nearest neighbors
    neighbors = lsh_model.approxNearestNeighbors(
        dataset=vector_df, key=query_vec, numNearestNeighbors=top_k + 1
    )

    result = neighbors.filter(F.col("id") != movie_id).select("id").limit(top_k)

    return [row["id"] for row in result.collect()]


# Create your views here.
def home(request):
    context = {}
    if request.method == "POST":
        # print("In post")
        movie_title = request.POST.get("movie_title")
        context["movie_title"] = movie_title
        # print(f"movie_title is {movie_title}")
        if movie_title:
            try:
                # Step 1: Find movie_id from title
                movie = MovieMetadata.objects.filter(title__iexact=movie_title).first()
                if not movie:
                    messages.error(
                        request, f"No movie found with title '{movie_title}'."
                    )
                    return redirect("/")

                movie_id = movie.id

                # print(f"id is {movie_id}")

                # Step 2: Get recommended ids
                rec_ids = get_recommendations(movie_id)
                # print(f"rec_ids is {rec_ids}")
                # Step 3: Fetch metadata for recommendations
                recommendations = list(
                    MovieMetadata.objects.filter(id__in=rec_ids).values(
                        "title", "poster_path", "release_year"
                    )
                )
                context["recommendations"] = recommendations
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                return redirect("/")

    return render(request, "home.html", context)


def grossing(request):
    # Top 25 grossing (all time)
    top25 = MasterTable.objects.order_by("-revenue")[:25].values(
        "id", "title", "poster_path", "release_year", "revenue"
    )

    # Yearly grossing (default 2024 or selected year)
    selected_year = int(request.GET.get("year", 2024))

    yearly_movies = list(
        MasterTable.objects.filter(release_year=selected_year)
        .order_by("-revenue")[:5]
        .values("title", "poster_path", "release_year", "revenue")
    )

    context = {
        "top25": top25,
        "yearly_movies": yearly_movies,
        "selected_year": selected_year,
        "years": range(2000, 2025),
    }

    return render(request, "grossing.html", context)


def analytics(request):
    
    # 1. Genre distribution (top 10)
    # Since genres_list is an ArrayField, annotate + unnest in DB is faster.
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT unnest(genres_list) as genre, COUNT(*) as count
            FROM master_table
            WHERE genres_list IS NOT NULL
            GROUP BY genre
            ORDER BY count DESC
            LIMIT 10;
        """
        )
        rows = cursor.fetchall()

    genre_labels = [r[0] for r in rows]
    genre_values = [r[1] for r in rows]

    # 2. Budget vs Revenue (scatter)
    # Filter out 0 / null budget & revenue
    budget_revenue = [
    {"x": row["budget"] / 1_000_000, "y": row["revenue"] / 1_000_000}
    for row in MasterTable.objects.filter(budget__gt=0, revenue__gt=0).values(
        "budget", "revenue"
    ) ]

    # 3. Revenue trends per year
    revenue_by_year = (
        MasterTable.objects.filter(revenue__gt=0, release_year__isnull=False)
        .values("release_year")
        .annotate(avg_revenue=Avg("revenue"))
        .order_by("release_year")
    )

    years = [r["release_year"] for r in revenue_by_year]
    avg_revenues = [
        round((r["avg_revenue"] or 0) / 1_000_000, 2) for r in revenue_by_year
    ]

    context = {
        "genre_labels": genre_labels,
        "genre_values": genre_values,
        "budget_revenue": budget_revenue,
        "years": years,
        "avg_revenues": avg_revenues,
    }
    return render(request, "analytics.html", context)
